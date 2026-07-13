# model/otp.py
# Model: Quản lý mã OTP

from datetime import datetime, timedelta
import random
import string

class OTP:
    _id_counter = 1

    def __init__(self, employee_id: int, email: str, code: str = None):
        self.id = OTP._id_counter
        OTP._id_counter += 1
        self.employee_id = employee_id
        self.email = email
        self.code = code or self.generate_otp()
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.expires_at = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        self.used = False

    @staticmethod
    def generate_otp() -> str:
        """Tạo mã OTP 6 chữ số"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self) -> bool:
        """Kiểm tra OTP đã hết hạn chưa"""
        now = datetime.now()
        expires = datetime.strptime(self.expires_at, "%Y-%m-%d %H:%M:%S")
        return now > expires

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "email": self.email,
            "code": self.code,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "used": self.used
        }

    @staticmethod
    def from_dict(data: dict) -> "OTP":
        otp = OTP.__new__(OTP)
        otp.id = data["id"]
        otp.employee_id = data["employee_id"]
        otp.email = data["email"]
        otp.code = data["code"]
        otp.created_at = data["created_at"]
        otp.expires_at = data["expires_at"]
        otp.used = data.get("used", False)
        return otp