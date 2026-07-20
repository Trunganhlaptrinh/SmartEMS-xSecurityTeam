# util/validation.py
# util: kiểm tra dữ liệu đầu vào từ request

import re
from datetime import datetime

class Validation:

    @staticmethod
    def check_not_empty(value: str, field_name: str) -> str:
        if not value or not value.strip():
            raise ValueError(f"{field_name} không được để trống")
        return value.strip()

    @staticmethod
    def check_name(value: str) -> str:
        value = Validation.check_not_empty(value, "Tên")
        if not re.match(r'^[A-Za-zÀ-ỹ\s]+$', value):
            raise ValueError("Tên chỉ được chứa chữ cái và khoảng trắng")
        return value

    @staticmethod
    def check_username(value: str) -> str:
        value = Validation.check_not_empty(value, "Tên đăng nhập")
        # Cho phép email (có @ và .) và các ký tự thông thường
        if not re.match(r'^[a-zA-Z0-9_.@\-.]{3,50}$', value):
            raise ValueError("Tên đăng nhập không hợp lệ")
        return value

    @staticmethod
    def check_password(value: str) -> str:
        if not value or len(value) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự")
        return value

    @staticmethod
    def check_role(value: str) -> str:
        value = Validation.check_not_empty(value, "Role")
        if value not in ["admin", "employee"]:
            raise ValueError("Role phải là 'admin' hoặc 'employee'")
        return value

    @staticmethod
    def check_date(value: str, field_name: str = "Ngày") -> str:
        value = Validation.check_not_empty(value, field_name)
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"{field_name} phải đúng định dạng YYYY-MM-DD")
        return value

    @staticmethod
    def check_month(value: str) -> str:
        value = Validation.check_not_empty(value, "Tháng")
        try:
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Tháng phải đúng định dạng YYYY-MM")
        return value

    @staticmethod
    def check_attendance_status(value: str) -> str:
        value = Validation.check_not_empty(value, "Trạng thái")
        if value not in ["present", "absent", "late"]:
            raise ValueError("Trạng thái phải là: present / absent / late")
        return value

    @staticmethod
    def check_money(value, field_name: str = "Số tiền") -> float:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} phải là số")
        if amount < 0:
            raise ValueError(f"{field_name} không được âm")
        return amount

    @staticmethod
    def check_date_range(from_date: str, to_date: str):
        d1 = datetime.strptime(from_date, "%Y-%m-%d")
        d2 = datetime.strptime(to_date, "%Y-%m-%d")
        if d1 > d2:
            raise ValueError("Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc")

    @staticmethod
    def check_in_list(value: str, allowed_list: list, field_name: str) -> str:
        value = Validation.check_not_empty(value, field_name)
        if value not in allowed_list:
            raise ValueError(f"{field_name} phải là: {', '.join(allowed_list)}")
        return value