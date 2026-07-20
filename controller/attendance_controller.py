# controller/attendance_controller.py
# controller: xử lý logic điểm danh

from flask import Blueprint, request, jsonify, session
from model.attendance import Attendance
from util.file_helper  import FileHelper
from util.validation   import Validation

attendance_bp = Blueprint("attendance", __name__)

# ========================
# ĐIỂM DANH (nhân viên tự điểm hoặc admin điểm cho người khác)
# POST /api/attendance
# ========================
@attendance_bp.route("", methods=["POST"])
def mark_attendance():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    try:
        date   = Validation.check_date(data.get("date", ""), "Ngày")
        status = Validation.check_attendance_status(data.get("status", ""))
        note   = data.get("note", "").strip()
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    # --- BẢO MẬT: Xác định employee_id dựa trên role ---
    # Nếu là admin, có thể điểm cho người khác qua employee_id
    # Nếu là nhân viên, bắt buộc điểm cho chính mình
    if session.get("role") == "admin":
        # Admin: lấy employee_id từ request, nếu không có thì dùng session
        target_id = data.get("employee_id")
        if target_id is None:
            target_id = session["employee_id"]
        else:
            try:
                target_id = int(target_id)
            except (ValueError, TypeError):
                return jsonify({"success": False, "message": "Employee ID không hợp lệ"}), 400
    else:
        # Nhân viên: chỉ được điểm cho chính mình
        target_id = session["employee_id"]

    # --- KIỂM TRA TRÙNG LẶP (bắt buộc ở backend) ---
    all_att = FileHelper.read_all("attendance")
    already = any(
        a["employee_id"] == target_id and a["date"] == date
        for a in all_att
    )
    if already:
        return jsonify({"success": False, "message": "Đã điểm danh ngày này rồi"}), 409

    att = Attendance(employee_id=target_id, date=date, status=status, note=note)
    FileHelper.append_item("attendance", att.to_dict())
    return jsonify({"success": True, "message": "Điểm danh thành công", "id": att.id}), 201


# ========================
# XEM DANH SÁCH ĐIỂM DANH
# GET /api/attendance?employee_id=&month=
# ========================
@attendance_bp.route("", methods=["GET"])
def get_attendance():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    all_att = FileHelper.read_all("attendance")

    emp_id_filter = request.args.get("employee_id")
    month_filter  = request.args.get("month")  # "YYYY-MM"

    result = all_att

    # --- BẢO MẬT: Nhân viên chỉ xem được dữ liệu của mình ---
    if session.get("role") != "admin":
        result = [a for a in result if a["employee_id"] == session["employee_id"]]
    elif emp_id_filter:
        try:
            result = [a for a in result if a["employee_id"] == int(emp_id_filter)]
        except ValueError:
            return jsonify({"success": False, "message": "Employee ID không hợp lệ"}), 400

    if month_filter:
        result = [a for a in result if a["date"].startswith(month_filter)]

    return jsonify({"success": True, "data": result})


# ========================
# CẬP NHẬT ĐIỂM DANH (chỉ admin)
# PUT /api/attendance/<id>
# ========================
@attendance_bp.route("/<int:att_id>", methods=["PUT"])
def update_attendance(att_id):
    # --- BẢO MẬT: Chỉ admin mới được sửa ---
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        status = Validation.check_attendance_status(data.get("status", ""))
        note   = data.get("note", "").strip()
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    all_att = FileHelper.read_all("attendance")
    for i, a in enumerate(all_att):
        if a["id"] == att_id:
            all_att[i]["status"] = status
            all_att[i]["note"]   = note
            FileHelper.write_all("attendance", all_att)
            return jsonify({"success": True, "message": "Cập nhật thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy bản ghi"}), 404