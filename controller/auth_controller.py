# controller/auth_controller.py
# controller: xử lý logic đăng nhập, đăng xuất, quản lý nhân viên

import random
from flask import Blueprint, request, jsonify, session, current_app
from model.employee import Employee
from model.otp import OTP
from util.file_helper import FileHelper
from util.auth_helper import AuthHelper
from util.validation import Validation
from util.email_helper import EmailHelper

auth_bp = Blueprint("auth", __name__)

# Số lần đăng nhập sai tối đa (bao gồm cả sai mật khẩu và sai OTP)
MAX_LOGIN_ATTEMPTS = 5


# ========================
# ĐĂNG NHẬP
# POST /api/auth/login
# ========================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    try:
        username = Validation.check_username(data.get("username", ""))
        password = Validation.check_password(data.get("password", ""))
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    employees = FileHelper.read_all("employees")
    found = None
    found_index = -1
    for i, emp_dict in enumerate(employees):
        if emp_dict["username"] == username:
            found = emp_dict
            found_index = i
            break

    if not found:
        current_app.logger.warning(f"Failed login attempt for non-existent username: {username}")
        return jsonify({"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu"}), 401

    # ============================================================
    # KIỂM TRA TÀI KHOẢN BỊ KHÓA
    # ============================================================
    if found.get("is_locked", False):
        return jsonify({
            "success": False, 
            "message": "Tài khoản đã bị khóa do đăng nhập sai quá nhiều lần. Vui lòng liên hệ Admin để mở khóa."
        }), 403

    # ============================================================
    # KIỂM TRA MẬT KHẨU
    # ============================================================
    if not AuthHelper.check_password(password, found["password_hash"]):
        current_app.logger.warning(f"Failed login attempt (wrong password) for username: {username}")
        # Tăng số lần đăng nhập sai
        login_attempts = found.get("login_attempts", 0) + 1
        employees[found_index]["login_attempts"] = login_attempts
        
        # Nếu vượt quá số lần cho phép và không phải admin -> khóa tài khoản
        if found["role"] != "admin" and login_attempts >= MAX_LOGIN_ATTEMPTS:
            employees[found_index]["is_locked"] = True
            FileHelper.write_all("employees", employees)
            return jsonify({
                "success": False, 
                "message": f"Tài khoản đã bị khóa do đăng nhập sai {MAX_LOGIN_ATTEMPTS} lần. Vui lòng liên hệ Admin để mở khóa."
            }), 403
        
        FileHelper.write_all("employees", employees)
        remaining = MAX_LOGIN_ATTEMPTS - login_attempts
        if remaining < 0:
            remaining = 0
        
        # Thông báo số lần còn lại
        if found["role"] == "admin":
            message = f"Sai tên đăng nhập hoặc mật khẩu. Còn {remaining} lần thử."
        else:
            message = f"Sai tên đăng nhập hoặc mật khẩu. Còn {remaining} lần thử trước khi tài khoản bị khóa."
            
        return jsonify({
            "success": False, 
            "message": message
        }), 401

    # ============================================================
    # ĐĂNG NHẬP THÀNH CÔNG -> RESET SỐ LẦN THỬ SAI
    # ============================================================
    employees[found_index]["login_attempts"] = 0
    employees[found_index]["is_locked"] = False
    FileHelper.write_all("employees", employees)

    # Admin -> Đăng nhập thẳng
    if found["role"] == "admin":
        session["employee_id"] = found["id"]
        session["role"] = found["role"]
        session["name"] = found["name"]
        session["otp_verified"] = True

        return jsonify({
            "success": True,
            "message": "Đăng nhập thành công",
            "require_otp": False,
            "employee": {
                "id": found["id"],
                "name": found["name"],
                "role": found["role"],
                "department": found["department"]
            }
        })

    # User Gmail -> Gửi OTP
    if "@gmail.com" in username.lower():
        if not EmailHelper.has_active_bot():
            return jsonify({
                "success": False,
                "message": "Hệ thống chưa cấu hình email bot. Vui lòng liên hệ Admin!"
            }), 503
        
        session["pending_employee_id"] = found["id"]
        session["pending_employee_index"] = found_index
        
        email = username
        
        # Xóa OTP cũ
        all_otps = FileHelper.read_all("otp_codes")
        all_otps = [o for o in all_otps if o["employee_id"] != found["id"]]
        FileHelper.write_all("otp_codes", all_otps)
        
        otp = OTP(employee_id=found["id"], email=email)
        FileHelper.append_item("otp_codes", otp.to_dict())
        
        email_sent = EmailHelper.send_otp_email(email, otp.code, found["name"])
        
        if not email_sent:
            return jsonify({
                "success": False,
                "message": "Không thể gửi mã OTP qua email. Vui lòng thử lại sau hoặc liên hệ Admin."
            }), 500
        
        return jsonify({
            "success": True,
            "message": f"Đã gửi mã OTP đến {email}",
            "require_otp": True,
            "employee_id": found["id"],
            "email": email,
            "expires_in": 300
        })

    # User nội bộ -> Đăng nhập thẳng
    session["employee_id"] = found["id"]
    session["role"] = found["role"]
    session["name"] = found["name"]
    session["otp_verified"] = True

    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công",
        "require_otp": False,
        "employee": {
            "id": found["id"],
            "name": found["name"],
            "role": found["role"],
            "department": found["department"]
        }
    })


# ========================
# ĐĂNG XUẤT
# ========================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Đã đăng xuất"})


# ========================
# KIỂM TRA SESSION
# ========================
@auth_bp.route("/me", methods=["GET"])
def me():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    return jsonify({
        "success": True,
        "employee_id": session["employee_id"],
        "role": session["role"],
        "name": session["name"]
    })


# ========================
# LẤY DANH SÁCH NHÂN VIÊN (chỉ admin)
# ========================
@auth_bp.route("/employees", methods=["GET"])
def get_employees():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    employees = FileHelper.read_all("employees")
    safe = [{k: v for k, v in e.items() if k != "password_hash"} for e in employees]
    return jsonify({"success": True, "data": safe})


# ========================
# THÊM NHÂN VIÊN (chỉ admin)
# ========================
@auth_bp.route("/employees", methods=["POST"])
def add_employee():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        username = data.get("username", "").strip()
        if not username:
            raise ValueError("Tên đăng nhập không được để trống")
        
        password = Validation.check_password(data.get("password", ""))
        name = Validation.check_name(data.get("name", ""))
        role = Validation.check_role(data.get("role", ""))
        department = Validation.check_not_empty(data.get("department", ""), "Phòng ban")
        base_salary = Validation.check_money(data.get("base_salary", 0), "Lương cơ bản")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    if "@gmail.com" in username.lower():
        if not EmailHelper.has_active_bot():
            return jsonify({
                "success": False, 
                "message": "Không thể tạo tài khoản Gmail vì chưa có Email Bot nào hoạt động! Vui lòng cấu hình Email Bot trước."
            }), 400

    employees = FileHelper.read_all("employees")
    if any(e["username"] == username for e in employees):
        return jsonify({"success": False, "message": "Tên đăng nhập đã tồn tại"}), 409

    emp = Employee(
        username=username,
        password_hash=AuthHelper.hash_password(password),
        name=name,
        role=role,
        department=department,
        base_salary=base_salary
    )
    FileHelper.append_item("employees", emp.to_dict())
    return jsonify({"success": True, "message": "Thêm nhân viên thành công", "id": emp.id}), 201


# ========================
# XÓA NHÂN VIÊN (chỉ admin)
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
            employees[i]["login_attempts"] = 0
            employees[i]["is_locked"] = False
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": "Đã reset mật khẩu và mở khóa tài khoản"})

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404


# ========================
# MỞ KHÓA TÀI KHOẢN (chỉ admin)
# POST /api/auth/employees/<int:emp_id>/unlock
# ========================
@auth_bp.route("/employees/<int:emp_id>/unlock", methods=["POST"])
def unlock_account(emp_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == emp_id:
            employees[i]["is_locked"] = False
            employees[i]["login_attempts"] = 0
            FileHelper.write_all("employees", employees)
            return jsonify({
                "success": True, 
                "message": f"Đã mở khóa tài khoản cho {emp.get('name', 'nhân viên')}"
            })

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404


# ========================
# XEM PROFILE CÁ NHÂN
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
# ========================
@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    employees = FileHelper.read_all("employees")

    for i, emp in enumerate(employees):
        if emp["id"] == session["employee_id"]:
            if data.get("name"):
                try:
                    employees[i]["name"] = Validation.check_name(data["name"])
                    session["name"] = employees[i]["name"]
                except ValueError as e:
                    return jsonify({"success": False, "message": str(e)}), 400

            if data.get("department"):
                employees[i]["department"] = data["department"].strip()

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
# ========================
@auth_bp.route("/profile/avatar", methods=["POST"])
def upload_avatar():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    avatar_base64 = data.get("avatar", "")

    if not avatar_base64 or not avatar_base64.startswith("data:image"):
        return jsonify({"success": False, "message": "Ảnh không hợp lệ"}), 400

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
# ADMIN CẬP NHẬT NHÂN VIÊN
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
            return jsonify({"success": True, "message": "Cập nhật thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404


# ========================
# UPLOAD ẢNH BÌA
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
# ========================
@auth_bp.route("/employees/<int:emp_id>", methods=["PUT"])
def update_employee(emp_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        name = Validation.check_name(data.get("name", ""))
        department = Validation.check_not_empty(data.get("department", ""), "Phòng ban")
        role = Validation.check_role(data.get("role", ""))
        base_salary = Validation.check_money(data.get("base_salary", 0), "Lương cơ bản")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    employees = FileHelper.read_all("employees")
    for i, emp in enumerate(employees):
        if emp["id"] == emp_id:
            employees[i]["name"] = name
            employees[i]["department"] = department
            employees[i]["role"] = role
            employees[i]["base_salary"] = base_salary
            FileHelper.write_all("employees", employees)
            return jsonify({"success": True, "message": "Cập nhật thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404


# ============================================================
# QUẢN LÝ EMAIL BOT (chỉ admin)
# ============================================================

@auth_bp.route("/email-bots", methods=["GET"])
def get_email_bots():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    bots = EmailHelper.get_bots()
    safe_bots = [{
        "sender": bot.get("sender", ""),
        "name": bot.get("name", ""),
        "is_active": bot.get("is_active", True),
        "created_at": bot.get("created_at", "")
    } for bot in bots]
    
    return jsonify({
        "success": True,
        "data": safe_bots,
        "has_active": EmailHelper.has_active_bot()
    })


@auth_bp.route("/email-bots", methods=["POST"])
def add_email_bot():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    sender = data.get("sender", "").strip()
    password = data.get("password", "").strip()
    name = data.get("name", "").strip()

    if not sender:
        return jsonify({"success": False, "message": "Vui lòng nhập email"}), 400
    if not password:
        return jsonify({"success": False, "message": "Vui lòng nhập mật khẩu ứng dụng"}), 400
    if "@" not in sender:
        return jsonify({"success": False, "message": "Email không hợp lệ"}), 400

    bots = EmailHelper.get_bots()
    for bot in bots:
        if bot["sender"] == sender:
            return jsonify({"success": False, "message": f"Email {sender} đã tồn tại"}), 409

    success = EmailHelper.add_bot(sender, password, name or sender)
    
    if success:
        return jsonify({"success": True, "message": f"Đã thêm email bot: {sender}"})
    return jsonify({"success": False, "message": "Lỗi lưu cấu hình"}), 500


@auth_bp.route("/email-bots/<path:sender>", methods=["PUT"])
def update_email_bot(sender):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    password = data.get("password", "").strip() if data.get("password") is not None else None
    name = data.get("name", "").strip() if data.get("name") is not None else None
    is_active = data.get("is_active", None)

    bots = EmailHelper.get_bots()
    if not any(bot["sender"] == sender for bot in bots):
        return jsonify({"success": False, "message": "Không tìm thấy email bot"}), 404

    if password is not None and not password:
        return jsonify({"success": False, "message": "Mật khẩu không được để trống"}), 400

    success = EmailHelper.update_bot(sender, password, name, is_active)
    
    if success:
        return jsonify({"success": True, "message": f"Đã cập nhật email bot: {sender}"})
    return jsonify({"success": False, "message": "Lỗi lưu cấu hình"}), 500


@auth_bp.route("/email-bots/<path:sender>", methods=["DELETE"])
def delete_email_bot(sender):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    bots = EmailHelper.get_bots()
    if not any(bot["sender"] == sender for bot in bots):
        return jsonify({"success": False, "message": "Không tìm thấy email bot"}), 404

    success = EmailHelper.delete_bot(sender)
    
    if success:
        return jsonify({"success": True, "message": f"Đã xóa email bot: {sender}"})
    return jsonify({"success": False, "message": "Lỗi xóa cấu hình"}), 500


@auth_bp.route("/email-bots/test", methods=["POST"])
def test_email_bot():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    test_email = data.get("test_email", "").strip()
    
    if not test_email or "@" not in test_email:
        return jsonify({"success": False, "message": "Email không hợp lệ"}), 400

    test_code = str(random.randint(100000, 999999))
    success = EmailHelper.send_otp_email(test_email, test_code, "Admin Test")
    
    if success:
        return jsonify({"success": True, "message": f"Đã gửi email test đến {test_email}"})
    return jsonify({"success": False, "message": "Gửi email test thất bại. Vui lòng kiểm tra cấu hình bot."}), 500