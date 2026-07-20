# controller/leave_controller.py
# controller: xử lý logic đơn xin nghỉ phép

from flask import Blueprint, request, jsonify, session
from model.leave      import Leave
from util.file_helper  import FileHelper
from util.validation   import Validation

def _attach_names(leaves: list) -> list:
    """Gắn employee_name vào mỗi đơn nghỉ dựa trên employee_id"""
    employees = FileHelper.read_all("employees")
    # tạo dict id → name để tra nhanh (giống HashMap trong Java)
    emp_map = {e["id"]: e["name"] for e in employees}
    for lv in leaves:
        lv["employee_name"] = emp_map.get(lv["employee_id"], f"ID {lv['employee_id']}")
    return leaves

leave_bp = Blueprint("leave", __name__)

# ========================
# GỬI ĐƠN XIN NGHỈ PHÉP
# POST /api/leave
# ========================
@leave_bp.route("", methods=["POST"])
def request_leave():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    try:
        from_date = Validation.check_date(data.get("from_date", ""), "Ngày bắt đầu")
        to_date   = Validation.check_date(data.get("to_date", ""),   "Ngày kết thúc")
        Validation.check_date_range(from_date, to_date)
        reason    = Validation.check_not_empty(data.get("reason", ""), "Lý do")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    lv = Leave(
        employee_id = session["employee_id"],
        from_date   = from_date,
        to_date     = to_date,
        reason      = reason
    )
    FileHelper.append_item("leaves", lv.to_dict())
    return jsonify({"success": True, "message": "Gửi đơn thành công", "id": lv.id}), 201

# ========================
# XEM DANH SÁCH ĐƠN NGHỈ PHÉP
# GET /api/leave?employee_id=&status=
# ========================
@leave_bp.route("", methods=["GET"])
def get_leaves():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    all_leaves = FileHelper.read_all("leaves")
    result     = all_leaves

    # nhân viên chỉ xem đơn của chính mình
    if session["role"] != "admin":
        result = [lv for lv in result if lv["employee_id"] == session["employee_id"]]
    else:
        emp_id_filter = request.args.get("employee_id")
        if emp_id_filter:
            result = [lv for lv in result if lv["employee_id"] == int(emp_id_filter)]

    status_filter = request.args.get("status")
    if status_filter:
        result = [lv for lv in result if lv["status"] == status_filter]

    # gắn tên nhân viên vào mỗi đơn trước khi trả về
    result = _attach_names(result)

    return jsonify({"success": True, "data": result})

# ========================
# DUYỆT / TỪ CHỐI ĐƠN (chỉ admin)
# PUT /api/leave/<id>
# ========================
@leave_bp.route("/<int:leave_id>", methods=["PUT"])
def update_leave(leave_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data   = request.get_json()
    status = data.get("status", "").strip()
    if status not in ["approved", "rejected", "pending"]:
        return jsonify({"success": False, "message": "Status phải là: approved / rejected / pending"}), 400

    all_leaves = FileHelper.read_all("leaves")
    for i, lv in enumerate(all_leaves):
        if lv["id"] == leave_id:
            all_leaves[i]["status"] = status
            FileHelper.write_all("leaves", all_leaves)
            return jsonify({"success": True, "message": f"Đã cập nhật trạng thái: {status}"})

    return jsonify({"success": False, "message": "Không tìm thấy đơn"}), 404

# ========================
# XÓA ĐƠN (chỉ khi pending, nhân viên tự xóa hoặc admin)
# DELETE /api/leave/<id>
# ========================
@leave_bp.route("/<int:leave_id>", methods=["DELETE"])
def delete_leave(leave_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    all_leaves = FileHelper.read_all("leaves")
    for lv in all_leaves:
        if lv["id"] == leave_id:
            # nhân viên chỉ được xóa đơn của mình và khi còn pending
            if session["role"] != "admin":
                if lv["employee_id"] != session["employee_id"]:
                    return jsonify({"success": False, "message": "Không có quyền"}), 403
                if lv["status"] != "pending":
                    return jsonify({"success": False, "message": "Chỉ được xóa đơn đang chờ duyệt"}), 400

            FileHelper.delete_item("leaves", leave_id)
            return jsonify({"success": True, "message": "Đã xóa đơn"})

    return jsonify({"success": False, "message": "Không tìm thấy đơn"}), 404