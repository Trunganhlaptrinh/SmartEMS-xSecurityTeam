# controller/contract_controller.py
# Controller: Quản lý hợp đồng dự án (Project Contract)
#
# Quy tắc phân quyền:
#   - Chỉ admin mới được thêm / sửa / xóa hợp đồng.
#   - Xem hợp đồng: chỉ admin HOẶC nhân viên nằm trong allowed_viewers
#     của hợp đồng đó (do admin chỉ định lúc tạo/sửa hợp đồng).
#     Là thành viên / owner của dự án KHÔNG mặc nhiên được xem hợp đồng.
#
# NÂNG CẤP:
#   - Giới hạn dung lượng + loại file khi upload hợp đồng, để tránh 1 file
#     quá to/sai định dạng làm phình & dễ hỏng data/contracts.json (từng là
#     nguyên nhân project_files.json bị lỗi JSON làm sập server).
#   - Ghi dữ liệu qua FileHelper.write_all_safe (có khóa) thay vì write_all
#     trực tiếp, để nhiều admin sửa hợp đồng cùng lúc không đè mất dữ liệu của nhau.

import base64
from datetime import datetime

from flask import Blueprint, request, jsonify, session, send_file
import io

from model.contract import Contract
from util.file_helper import FileHelper

contract_bp = Blueprint("contract", __name__)

# Blueprint riêng cho trang "Hợp đồng" ở sidebar — xem TẤT CẢ hợp đồng
# (không giới hạn trong 1 dự án cụ thể), vẫn áp dụng đúng luật phân quyền
# admin / allowed_viewers như các route bên dưới.
contract_list_bp = Blueprint("contract_list", __name__)

# ========================
# GIỚI HẠN FILE ĐÍNH KÈM
# ========================
MAX_FILE_SIZE_MB = 15
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "jpg", "jpeg", "png", "zip", "rar", "txt"
}


def _validate_uploaded_file(file_name: str, file_content: str):
    """Kiểm tra file hợp đồng trước khi lưu.
    Trả về (ok: bool, message: str)."""
    if not file_content:
        return True, ""  # không bắt buộc phải có file

    if not file_name or "." not in file_name:
        return False, "File phải có tên và phần mở rộng hợp lệ"

    ext = file_name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, (
            f"Định dạng .{ext} không được hỗ trợ. "
            f"Chỉ chấp nhận: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    content = file_content
    if content.startswith("data:"):
        content = content.split(",", 1)[1] if "," in content else content

    # ước lượng dung lượng thật từ độ dài base64 (base64 dài hơn ~33% so với gốc)
    approx_bytes = len(content) * 3 / 4
    if approx_bytes > MAX_FILE_SIZE_BYTES:
        return False, f"File vượt quá giới hạn {MAX_FILE_SIZE_MB}MB cho phép"

    return True, ""


# ========================
# HÀM PHỤ TRỢ
# ========================

def _get_project_or_none(project_id):
    projects = FileHelper.read_all("projects")
    return next((p for p in projects if p["id"] == project_id), None)


def _can_view_contract(contract: dict) -> bool:
    """Chỉ admin hoặc người được chỉ định (allowed_viewers) mới được xem."""
    if session.get("role") == "admin":
        return True
    return session.get("employee_id") in contract.get("allowed_viewers", [])


# ========================
# DANH SÁCH HỢP ĐỒNG CỦA 1 DỰ ÁN
# ========================

@contract_bp.route("/<int:project_id>/contracts", methods=["GET"])
def get_contracts(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        project = _get_project_or_none(project_id)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404

        contracts = FileHelper.read_all("contracts")
        contracts = [c for c in contracts if c["project_id"] == project_id]

        # lọc theo quyền xem: admin thấy hết, người khác chỉ thấy hợp đồng
        # mà mình có tên trong allowed_viewers
        if session.get("role") != "admin":
            contracts = [c for c in contracts
                         if session["employee_id"] in c.get("allowed_viewers", [])]

        # không trả file_content (base64) trong danh sách để nhẹ payload
        for c in contracts:
            c.pop("file_content", None)

        contracts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jsonify({"success": True, "data": contracts})
    except Exception as e:
        print("Lỗi get_contracts:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# CHI TIẾT 1 HỢP ĐỒNG
# ========================

@contract_bp.route("/<int:project_id>/contracts/<int:contract_id>", methods=["GET"])
def get_contract(project_id, contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        contracts = FileHelper.read_all("contracts")
        contract = next((c for c in contracts
                          if c["id"] == contract_id and c["project_id"] == project_id), None)
        if not contract:
            return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404

        if not _can_view_contract(contract):
            return jsonify({"success": False, "message": "Không có quyền xem hợp đồng này"}), 403

        contract = dict(contract)
        contract.pop("file_content", None)
        return jsonify({"success": True, "data": contract})
    except Exception as e:
        print("Lỗi get_contract:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# TẢI FILE HỢP ĐỒNG
# ========================

@contract_bp.route("/<int:project_id>/contracts/<int:contract_id>/download", methods=["GET"])
def download_contract(project_id, contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        contracts = FileHelper.read_all("contracts")
        contract = next((c for c in contracts
                          if c["id"] == contract_id and c["project_id"] == project_id), None)
        if not contract:
            return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404

        if not _can_view_contract(contract):
            return jsonify({"success": False, "message": "Không có quyền xem hợp đồng này"}), 403

        content = contract.get("file_content", "")
        if not content:
            return jsonify({"success": False, "message": "Hợp đồng này chưa có file đính kèm"}), 404

        if content.startswith("data:"):
            content = content.split(",", 1)[1] if "," in content else content

        file_bytes = base64.b64decode(content)
        filename = contract.get("file_name") or f"hop_dong_{contract_id}"

        return send_file(
            io.BytesIO(file_bytes),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print("Lỗi download_contract:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# TẠO HỢP ĐỒNG (chỉ admin)
# ========================

@contract_bp.route("/<int:project_id>/contracts", methods=["POST"])
def create_contract(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ admin mới được thêm hợp đồng"}), 403

    try:
        project = _get_project_or_none(project_id)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404

        data = request.get_json()
        title = data.get("title", "").strip()
        if not title:
            return jsonify({"success": False, "message": "Tên hợp đồng không được để trống"}), 400

        allowed_viewers = data.get("allowed_viewers", [])
        if not isinstance(allowed_viewers, list):
            return jsonify({"success": False, "message": "Danh sách người được xem không hợp lệ"}), 400
        # đảm bảo toàn bộ là số nguyên (employee_id)
        try:
            allowed_viewers = [int(v) for v in allowed_viewers]
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Danh sách người được xem không hợp lệ"}), 400

        file_name = data.get("file_name", "").strip()
        file_content = data.get("file_content", "")
        ok, msg = _validate_uploaded_file(file_name, file_content)
        if not ok:
            return jsonify({"success": False, "message": msg}), 400

        employees = FileHelper.read_all("employees")
        author = next((e for e in employees if e["id"] == session["employee_id"]), None)
        author_name = author["name"] if author else "Administrator"

        contract = Contract(
            project_id=project_id,
            title=title,
            description=data.get("description", "").strip(),
            created_by=session["employee_id"],
            created_by_name=author_name,
            file_name=file_name,
            file_content=file_content,
            allowed_viewers=allowed_viewers
        )

        FileHelper.append_item("contracts", contract.to_dict())
        return jsonify({"success": True, "message": "Thêm hợp đồng thành công", "id": contract.id}), 201
    except Exception as e:
        print("Lỗi create_contract:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# SỬA HỢP ĐỒNG (chỉ admin)
# ========================

@contract_bp.route("/<int:project_id>/contracts/<int:contract_id>", methods=["PUT"])
def update_contract(project_id, contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ admin mới được sửa hợp đồng"}), 403

    try:
        data = request.get_json()
        title = data.get("title", "").strip()
        if not title:
            return jsonify({"success": False, "message": "Tên hợp đồng không được để trống"}), 400

        allowed_viewers = data.get("allowed_viewers", [])
        if not isinstance(allowed_viewers, list):
            return jsonify({"success": False, "message": "Danh sách người được xem không hợp lệ"}), 400
        try:
            allowed_viewers = [int(v) for v in allowed_viewers]
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Danh sách người được xem không hợp lệ"}), 400

        new_file_name = data.get("file_name", "").strip()
        new_file_content = data.get("file_content", "")
        if new_file_content:
            ok, msg = _validate_uploaded_file(new_file_name, new_file_content)
            if not ok:
                return jsonify({"success": False, "message": msg}), 400

        contracts = FileHelper.read_all("contracts")
        for i, c in enumerate(contracts):
            if c["id"] == contract_id and c["project_id"] == project_id:
                contracts[i]["title"] = title
                contracts[i]["description"] = data.get("description", "").strip()
                contracts[i]["allowed_viewers"] = allowed_viewers
                # chỉ cập nhật file nếu người dùng có gửi file mới lên
                if new_file_content:
                    contracts[i]["file_name"] = new_file_name
                    contracts[i]["file_content"] = new_file_content
                    contracts[i]["file_size"] = len(new_file_content)
                contracts[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # ghi có khóa (lock) để 2 admin sửa cùng lúc không đè mất dữ liệu nhau
                FileHelper.write_all_safe("contracts", contracts)
                return jsonify({"success": True, "message": "Cập nhật hợp đồng thành công"})

        return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404
    except Exception as e:
        print("Lỗi update_contract:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# XÓA HỢP ĐỒNG (chỉ admin)
# ========================

@contract_bp.route("/<int:project_id>/contracts/<int:contract_id>", methods=["DELETE"])
def delete_contract(project_id, contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ admin mới được xóa hợp đồng"}), 403

    try:
        contracts = FileHelper.read_all("contracts")
        contract = next((c for c in contracts
                          if c["id"] == contract_id and c["project_id"] == project_id), None)
        if not contract:
            return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404

        ok = FileHelper.delete_item("contracts", contract_id)
        if not ok:
            return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404
        return jsonify({"success": True, "message": "Đã xóa hợp đồng"})
    except Exception as e:
        print("Lỗi delete_contract:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# DANH SÁCH TẤT CẢ HỢP ĐỒNG (trang "Hợp đồng" riêng ở sidebar)
# ========================

@contract_list_bp.route("", methods=["GET"])
def get_all_contracts():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        contracts = FileHelper.read_all("contracts")

        # cùng luật phân quyền như trong 1 dự án: admin thấy hết,
        # người khác chỉ thấy hợp đồng mình được chỉ định (allowed_viewers)
        if session.get("role") != "admin":
            contracts = [c for c in contracts
                         if session["employee_id"] in c.get("allowed_viewers", [])]

        for c in contracts:
            c.pop("file_content", None)

        projects = FileHelper.read_all("projects")
        proj_map = {p["id"]: p["name"] for p in projects}
        for c in contracts:
            c["project_name"] = proj_map.get(c["project_id"], f"Dự án #{c['project_id']}")

        search = request.args.get("search", "").strip().lower()
        if search:
            contracts = [c for c in contracts if search in c.get("title", "").lower()
                         or search in c.get("project_name", "").lower()]

        contracts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jsonify({"success": True, "data": contracts})
    except Exception as e:
        print("Lỗi get_all_contracts:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500