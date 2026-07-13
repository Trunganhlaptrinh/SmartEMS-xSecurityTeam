# controller/otp_controller.py
# Controller: Xác thực OTP

from flask import Blueprint, request, jsonify, session
from model.otp import OTP
from util.file_helper import FileHelper
from util.email_helper import EmailHelper
from datetime import datetime

otp_bp = Blueprint("otp", __name__)

# Số lần OTP sai tối đa (khóa tài khoản)
MAX_OTP_ATTEMPTS = 5


@otp_bp.route("/send", methods=["POST"])
def send_otp():
    """
    Gửi mã OTP đến email của user
    POST /api/otp/send
    Body: { "employee_id": 1 }
    """
    data = request.get_json()
    employee_id = data.get("employee_id")
    
    if not employee_id:
        return jsonify({"success": False, "message": "Thiếu employee_id"}), 400
    
    employees = FileHelper.read_all("employees")
    emp = next((e for e in employees if e["id"] == employee_id), None)
    
    if not emp:
        return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404
    
    # Kiểm tra tài khoản bị khóa
    if emp.get("is_locked", False):
        return jsonify({
            "success": False, 
            "message": "Tài khoản đã bị khóa. Vui lòng liên hệ Admin để mở khóa."
        }), 403
    
    email = emp.get("email")
    if not email:
        if "@" in emp["username"]:
            email = emp["username"]
        else:
            email = f"{emp['username']}@smartems.com"
    
    print(f"Gửi OTP cho {emp['name']} ({emp['username']}) -> {email}")
    
    all_otps = FileHelper.read_all("otp_codes")
    all_otps = [o for o in all_otps if o["employee_id"] != employee_id]
    FileHelper.write_all("otp_codes", all_otps)
    
    otp = OTP(employee_id=employee_id, email=email)
    FileHelper.append_item("otp_codes", otp.to_dict())
    
    success = EmailHelper.send_otp_email(email, otp.code, emp["name"])
    
    return jsonify({
        "success": True,
        "message": f"Đã gửi mã OTP đến {email}",
        "employee_id": employee_id,
        "expires_in": 300,
        "debug_code": otp.code if not success else None
    })


@otp_bp.route("/verify", methods=["POST"])
def verify_otp():
    """
    Xác thực mã OTP
    POST /api/otp/verify
    Body: { "employee_id": 1, "code": "123456" }
    
    Nếu sai OTP 5 lần -> khóa tài khoản
    """
    data = request.get_json()
    employee_id = data.get("employee_id")
    code = data.get("code", "").strip()
    
    if not employee_id or not code:
        return jsonify({"success": False, "message": "Thiếu thông tin"}), 400
    
    # Lấy thông tin user
    employees = FileHelper.read_all("employees")
    emp_index = -1
    emp = None
    for i, e in enumerate(employees):
        if e["id"] == employee_id:
            emp = e
            emp_index = i
            break
    
    if not emp:
        return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404
    
    # Kiểm tra tài khoản bị khóa
    if emp.get("is_locked", False):
        return jsonify({
            "success": False, 
            "message": "Tài khoản đã bị khóa. Vui lòng liên hệ Admin để mở khóa."
        }), 403
    
    # Tìm OTP
    all_otps = FileHelper.read_all("otp_codes")
    otp_data = None
    
    for o in all_otps:
        if o["employee_id"] == employee_id and o["code"] == code and not o.get("used", False):
            otp_data = o
            break
    
    if not otp_data:
        # OTP sai - Tăng số lần đăng nhập sai
        login_attempts = emp.get("login_attempts", 0) + 1
        employees[emp_index]["login_attempts"] = login_attempts
        
        # Nếu vượt quá số lần cho phép -> khóa tài khoản
        if login_attempts >= MAX_OTP_ATTEMPTS:
            employees[emp_index]["is_locked"] = True
            FileHelper.write_all("employees", employees)
            return jsonify({
                "success": False, 
                "message": f"Tài khoản đã bị khóa do nhập sai OTP {MAX_OTP_ATTEMPTS} lần. Vui lòng liên hệ Admin để mở khóa."
            }), 403
        
        FileHelper.write_all("employees", employees)
        remaining = MAX_OTP_ATTEMPTS - login_attempts
        return jsonify({
            "success": False, 
            "message": f"Mã OTP không hợp lệ. Còn {remaining} lần thử trước khi tài khoản bị khóa."
        }), 400
    
    # Kiểm tra hết hạn
    otp_obj = OTP.from_dict(otp_data)
    if otp_obj.is_expired():
        # OTP hết hạn cũng tính là sai
        login_attempts = emp.get("login_attempts", 0) + 1
        employees[emp_index]["login_attempts"] = login_attempts
        
        if login_attempts >= MAX_OTP_ATTEMPTS:
            employees[emp_index]["is_locked"] = True
            FileHelper.write_all("employees", employees)
            return jsonify({
                "success": False, 
                "message": f"Tài khoản đã bị khóa do nhập sai OTP {MAX_OTP_ATTEMPTS} lần. Vui lòng liên hệ Admin để mở khóa."
            }), 403
        
        FileHelper.write_all("employees", employees)
        remaining = MAX_OTP_ATTEMPTS - login_attempts
        return jsonify({
            "success": False, 
            "message": f"Mã OTP đã hết hạn. Còn {remaining} lần thử trước khi tài khoản bị khóa."
        }), 400
    
    # Đánh dấu đã sử dụng
    for i, o in enumerate(all_otps):
        if o["id"] == otp_data["id"]:
            all_otps[i]["used"] = True
            break
    
    FileHelper.write_all("otp_codes", all_otps)
    
    # OTP đúng - Reset số lần thử sai và mở khóa nếu có
    employees[emp_index]["login_attempts"] = 0
    employees[emp_index]["is_locked"] = False
    FileHelper.write_all("employees", employees)
    
    # Đăng nhập thành công
    session["employee_id"] = emp["id"]
    session["role"] = emp["role"]
    session["name"] = emp["name"]
    session["otp_verified"] = True
    
    return jsonify({
        "success": True,
        "message": "Xác thực thành công",
        "employee": {
            "id": emp["id"],
            "name": emp["name"],
            "role": emp["role"],
            "department": emp["department"]
        }
    })


@otp_bp.route("/resend", methods=["POST"])
def resend_otp():
    """
    Gửi lại mã OTP
    POST /api/otp/resend
    Body: { "employee_id": 1 }
    """
    data = request.get_json()
    employee_id = data.get("employee_id")
    
    if not employee_id:
        return jsonify({"success": False, "message": "Thiếu employee_id"}), 400
    
    all_otps = FileHelper.read_all("otp_codes")
    all_otps = [o for o in all_otps if o["employee_id"] != employee_id]
    FileHelper.write_all("otp_codes", all_otps)
    
    return send_otp()