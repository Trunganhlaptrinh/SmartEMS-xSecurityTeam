# controller/auth_controller.py
# controller: xử lý logic đăng nhập, đăng xuất, quản lý nhân viên
# tương tự StudentManagement.java — nhưng trả về JSON thay vì in ra console

from flask import Blueprint, request, jsonify, session
from model.employee   import Employee
from util.file_helper import FileHelper
from util.auth_helper import AuthHelper
from util.validation  import Validation

# Blueprint = nhóm các route liên quan đến auth
# tương tự: class StudentManagement trong Java
auth_bp = Blueprint("auth", __name__)

# ========================
# ĐĂNG NHẬP
# POST /api/auth/login
# ========================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # kiểm tra input
    try:
        username = Validation.check_username(data.get("username", ""))
        password = Validation.check_password(data.get("password", ""))
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    # tìm nhân viên theo username trong file JSON
    employees = FileHelper.read_all("employees")
    found = None
    for emp_dict in employees:
        if emp_dict["username"] == username:
            found = emp_dict
            break

    # kiểm tra tồn tại và mật khẩu
    if not found or not AuthHelper.check_password(password, found["password_hash"]):
        return jsonify({"success": False, "message": "Sai username hoặc mật khẩu"}), 401

    # lưu thông tin vào session (giữ đăng nhập)
    session["employee_id"] = found["id"]
    session["role"]        = found["role"]
    session["name"]        = found["name"]

    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công",
        "employee": {
            "id":         found["id"],
            "name":       found["name"],
            "role":       found["role"],
            "department": found["department"]
        }
    })

# ========================
# ĐĂNG XUẤT
# POST /api/auth/logout
# ========================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Đã đăng xuất"})

# ========================
# KIỂM TRA SESSION
# GET /api/auth/me
# ========================
@auth_bp.route("/me", methods=["GET"])
def me():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    return jsonify({
        "success":     True,
        "employee_id": session["employee_id"],
        "role":        session["role"],
        "name":        session["name"]
    })

# ========================
# LẤY DANH SÁCH NHÂN VIÊN (chỉ admin)
# GET /api/auth/employees
# ========================
@auth_bp.route("/employees", methods=["GET"])
def get_employees():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    employees = FileHelper.read_all("employees")
    # không trả về password_hash ra ngoài
    safe = [{k: v for k, v in e.items() if k != "password_hash"} for e in employees]
    return jsonify({"success": True, "data": safe})

# ========================
# THÊM NHÂN VIÊN (chỉ admin)
# POST /api/auth/employees
# ========================
@auth_bp.route("/employees", methods=["POST"])
def add_employee():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        username   = Validation.check_username(data.get("username", ""))
        password   = Validation.check_password(data.get("password", ""))
        name       = Validation.check_name(data.get("name", ""))
        role       = Validation.check_role(data.get("role", ""))
        department = Validation.check_not_empty(data.get("department", ""), "Phòng ban")
        base_salary = Validation.check_money(data.get("base_salary", 0), "Lương cơ bản")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    # kiểm tra username trùng
    employees = FileHelper.read_all("employees")
    if any(e["username"] == username for e in employees):
        return jsonify({"success": False, "message": "Username đã tồn tại"}), 409

    emp = Employee(
        username      = username,
        password_hash = AuthHelper.hash_password(password),
        name          = name,
        role          = role,
        department    = department,
        base_salary   = base_salary
    )
    FileHelper.append_item("employees", emp.to_dict())
    return jsonify({"success": True, "message": "Thêm nhân viên thành công", "id": emp.id}), 201

# ========================
# XÓA NHÂN VIÊN (chỉ admin)
# DELETE /api/auth/employees/<id>
# ========================
@auth_bp.route("/employees/<int:emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403
    if emp_id == session.get("employee_id"):
        return jsonify({"success": False, "message": "Không thể xóa chính mình"}), 400

    ok = FileHelper.delete_item("employees", emp_id)
    if not ok:
        return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404
    return jsonify({"success": True, "message": "Đã xóa nhân viên"})

# ========================
# RESET MẬT KHẨU (chỉ admin)
# PUT /api/auth/employees/<id>/reset-password
# ========================
@auth_bp.route("/employees/<int:emp_id>/reset-password", methods=["PUT"])
def reset_password(emp_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        new_password = Validation.check_password(data.get("new_password", ""))
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == emp_id:
            employees[i]["password_hash"] = AuthHelper.hash_password(new_password)
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": f"Đã reset mật khẩu thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404

# ========================
# XEM PROFILE CÁ NHÂN
# GET /api/auth/profile
# ========================
@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    employees = FileHelper.read_all("employees")
    emp = next((e for e in employees if e["id"] == session["employee_id"]), None)
    if not emp:
        return jsonify({"success": False, "message": "Không tìm thấy"}), 404

    safe = {k: v for k, v in emp.items() if k != "password_hash"}
    return jsonify({"success": True, "data": safe})

# ========================
# CẬP NHẬT PROFILE
# PUT /api/auth/profile
# ========================
@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    employees = FileHelper.read_all("employees")

    for i, emp in enumerate(employees):
        if emp["id"] == session["employee_id"]:
            # chỉ cho sửa name, department (không cho sửa role, username)
            if data.get("name"):
                try:
                    employees[i]["name"] = Validation.check_name(data["name"])
                    session["name"]      = employees[i]["name"]
                except ValueError as e:
                    return jsonify({"success": False, "message": str(e)}), 400

            if data.get("department"):
                employees[i]["department"] = data["department"].strip()

            # đổi mật khẩu nếu có gửi lên
            if data.get("new_password"):
                try:
                    Validation.check_password(data["new_password"])
                except ValueError as e:
                    return jsonify({"success": False, "message": str(e)}), 400

                old_pw = data.get("old_password", "")
                if not AuthHelper.check_password(old_pw, emp["password_hash"]):
                    return jsonify({"success": False, "message": "Mật khẩu cũ không đúng"}), 400

                if data["new_password"] != data.get("confirm_password", ""):
                    return jsonify({"success": False, "message": "Mật khẩu xác nhận không khớp"}), 400

                employees[i]["password_hash"] = AuthHelper.hash_password(data["new_password"])

            FileHelper.write_all("employees", employees)
            safe = {k: v for k, v in employees[i].items() if k != "password_hash"}
            return jsonify({"success": True, "message": "Cập nhật thành công", "data": safe})

    return jsonify({"success": False, "message": "Không tìm thấy"}), 404


# ========================
# UPLOAD ẢNH ĐẠI DIỆN
# POST /api/auth/profile/avatar
# ========================
@auth_bp.route("/profile/avatar", methods=["POST"])
def upload_avatar():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    avatar_base64 = data.get("avatar", "")

    if not avatar_base64 or not avatar_base64.startswith("data:image"):
        return jsonify({"success": False, "message": "Ảnh không hợp lệ"}), 400

    # giới hạn dung lượng ~2MB
    if len(avatar_base64) > 2 * 1024 * 1024 * 1.4:
        return jsonify({"success": False, "message": "Ảnh quá lớn, vui lòng chọn ảnh dưới 2MB"}), 400

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == session["employee_id"]:
            employees[i]["avatar"] = avatar_base64
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": "Cập nhật ảnh thành công", "avatar": avatar_base64})

    return jsonify({"success": False, "message": "Không tìm thấy"}), 404

# ========================
# LẤY ẢNH ĐẠI DIỆN
# GET /api/auth/profile/avatar
# ========================
@auth_bp.route("/profile/avatar", methods=["GET"])
def get_avatar():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    employees = FileHelper.read_all("employees")
    emp = next((e for e in employees if e["id"] == session["employee_id"]), None)
    if not emp:
        return jsonify({"success": False, "message": "Không tìm thấy"}), 404

    return jsonify({"success": True, "avatar": emp.get("avatar", "")})



# ========================
# ADMIN CẬP NHẬT NHÂN VIÊN (Lương CB + Phòng ban)
# PUT /api/auth/profile/admin-update
# ========================
@auth_bp.route("/profile/admin-update", methods=["PUT"])
def admin_update_employee():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    employee_id = data.get("employee_id")
    
    if not employee_id:
        return jsonify({"success": False, "message": "Thiếu ID nhân viên"}), 400

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == employee_id:
            if "base_salary" in data:
                try:
                    employees[i]["base_salary"] = float(data["base_salary"])
                except (ValueError, TypeError):
                    return jsonify({"success": False, "message": "Lương cơ bản không hợp lệ"}), 400
            
            if "department" in data and data["department"].strip():
                employees[i]["department"] = data["department"].strip()
            
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": "Cập nhật thông tin nhân viên thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404



# ========================
# UPLOAD ẢNH BÌA
# POST /api/auth/profile/cover
# ========================
@auth_bp.route("/profile/cover", methods=["POST"])
def upload_cover():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    cover_base64 = data.get("cover", "")

    if not cover_base64 or not cover_base64.startswith("data:image"):
        return jsonify({"success": False, "message": "Ảnh không hợp lệ"}), 400

    if len(cover_base64) > 5 * 1024 * 1024 * 1.4:
        return jsonify({"success": False, "message": "Ảnh quá lớn, vui lòng chọn ảnh dưới 5MB"}), 400

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == session["employee_id"]:
            employees[i]["cover"] = cover_base64
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": "Cập nhật ảnh bìa thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy"}), 404


# ========================
# CẬP NHẬT NHÂN VIÊN (chỉ admin)
# PUT /api/auth/employees/<id>
# ========================
@auth_bp.route("/employees/<int:emp_id>", methods=["PUT"])
def update_employee(emp_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        name       = Validation.check_name(data.get("name", ""))
        department = Validation.check_not_empty(data.get("department", ""), "Phòng ban")
        role       = Validation.check_role(data.get("role", ""))
        base_salary = Validation.check_money(data.get("base_salary", 0), "Lương cơ bản")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == emp_id:
            employees[i]["name"]        = name
            employees[i]["department"]  = department
            employees[i]["role"]        = role
            employees[i]["base_salary"] = base_salary
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": "Cập nhật nhân viên thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404