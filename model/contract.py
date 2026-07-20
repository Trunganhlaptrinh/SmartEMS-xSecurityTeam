# controller/contract_controller.py
# Controller: Quản lý hợp đồng (chỉ admin)

from flask import Blueprint, request, jsonify, session, send_file
from model.contract import Contract
from util.file_helper import FileHelper
from util.validation import Validation
import os
import base64
import io
from datetime import datetime

# Tạo blueprint
contract_bp = Blueprint("contract", __name__)

# Thư mục lưu file hợp đồng
CONTRACT_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "data", 
    "contracts"
)

# Đảm bảo thư mục tồn tại
os.makedirs(CONTRACT_UPLOAD_DIR, exist_ok=True)

# Giới hạn kích thước file (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Danh sách loại file cho phép
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.zip', '.rar'}


def get_safe_filename(filename: str) -> str:
    """Tạo tên file an toàn để lưu trên server"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    safe_name = f"{timestamp}_{id_generator()}{ext}"
    return safe_name


def id_generator():
    """Tạo ID ngẫu nhiên cho tên file"""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


# ========================
# LẤY DANH SÁCH HỢP ĐỒNG
# GET /api/contracts
# ========================
@contract_bp.route("", methods=["GET"])
def get_contracts():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    
    # Chỉ admin mới xem được
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403
    
    contracts = FileHelper.read_all("contracts")
    # Lọc chỉ lấy active
    contracts = [c for c in contracts if c.get("status") == "active"]
    # Sắp xếp mới nhất lên đầu
    contracts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return jsonify({"success": True, "data": contracts})


# ========================
# UPLOAD FILE HỢP ĐỒNG
# POST /api/contracts/upload
# ========================
@contract_bp.route("/upload", methods=["POST"])
def upload_contract():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403
    
    # Kiểm tra file trong request
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file"}), 400
    
    file = request.files['file']
    name = request.form.get('name', '').strip()
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Chưa chọn file"}), 400
    
    if not name:
        name = file.filename
    
    # Kiểm tra kích thước file
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({
            "success": False, 
            "message": f"File quá lớn. Giới hạn {MAX_FILE_SIZE // (1024*1024)}MB"
        }), 400
    
    # Kiểm tra loại file
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "success": False, 
            "message": f"Loại file không được hỗ trợ. Hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    # Lưu file
    safe_filename = get_safe_filename(file.filename)
    file_path = os.path.join(CONTRACT_UPLOAD_DIR, safe_filename)
    file.save(file_path)
    
    # Lấy thông tin người upload
    employees = FileHelper.read_all("employees")
    uploader = next((e for e in employees if e["id"] == session["employee_id"]), None)
    uploader_name = uploader["name"] if uploader else "Admin"
    
    # Tạo bản ghi contract
    contract = Contract(
        name=name,
        filename=safe_filename,
        file_size=file_size,
        uploader_id=session["employee_id"],
        uploader_name=uploader_name
    )
    
    # Lưu metadata
    FileHelper.append_item("contracts", contract.to_dict())
    
    return jsonify({
        "success": True, 
        "message": f"Đã upload file '{name}' thành công",
        "data": contract.to_dict()
    }), 201


# ========================
# TẢI FILE HỢP ĐỒNG
# GET /api/contracts/download/<id>
# ========================
@contract_bp.route("/download/<int:contract_id>", methods=["GET"])
def download_contract(contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403
    
    # Tìm contract
    contracts = FileHelper.read_all("contracts")
    contract = next((c for c in contracts if c["id"] == contract_id), None)
    
    if not contract:
        return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404
    
    if contract.get("status") != "active":
        return jsonify({"success": False, "message": "Hợp đồng đã bị xóa"}), 404
    
    # Kiểm tra file tồn tại
    file_path = os.path.join(CONTRACT_UPLOAD_DIR, contract["filename"])
    
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "File không tồn tại trên server"}), 404
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=contract.get("name", contract["filename"]),
            mimetype="application/octet-stream"
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tải file: {str(e)}"}), 500


# ========================
# XÓA HỢP ĐỒNG (soft delete)
# DELETE /api/contracts/<id>
# ========================
@contract_bp.route("/<int:contract_id>", methods=["DELETE"])
def delete_contract(contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403
    
    contracts = FileHelper.read_all("contracts")
    
    for i, c in enumerate(contracts):
        if c["id"] == contract_id:
            # Soft delete: chuyển status thành archived
            contracts[i]["status"] = "archived"
            FileHelper.write_all("contracts", contracts)
            
            # Xóa file vật lý (tùy chọn)
            # file_path = os.path.join(CONTRACT_UPLOAD_DIR, c["filename"])
            # if os.path.exists(file_path):
            #     os.remove(file_path)
            
            return jsonify({"success": True, "message": "Đã xóa hợp đồng"})
    
    return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404


# ========================
# CẬP NHẬT TÊN HỢP ĐỒNG
# PUT /api/contracts/<id>
# ========================
@contract_bp.route("/<int:contract_id>", methods=["PUT"])
def update_contract(contract_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403
    
    data = request.get_json()
    name = data.get("name", "").strip()
    
    if not name:
        return jsonify({"success": False, "message": "Tên không được để trống"}), 400
    
    contracts = FileHelper.read_all("contracts")
    
    for i, c in enumerate(contracts):
        if c["id"] == contract_id:
            contracts[i]["name"] = name
            FileHelper.write_all("contracts", contracts)
            return jsonify({"success": True, "message": "Đã cập nhật tên hợp đồng"})
    
    return jsonify({"success": False, "message": "Không tìm thấy hợp đồng"}), 404