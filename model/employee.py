# model/employee.py
# model: lưu trữ thông tin nhân viên (thuộc tính, constructor, getter/setter)

class Employee:
    # Biến class dùng để tự tăng ID
    _id_counter = 1

    def __init__(self, username: str, password_hash: str, name: str, role: str, department: str, base_salary: float):
        self.id = Employee._id_counter
        Employee._id_counter += 1

        self.username = username          # tài khoản đăng nhập
        self.password_hash = password_hash # mật khẩu đã hash
        self.name = name                  # tên hiển thị
        self.role = role                  # "admin" hoặc "employee"
        self.department = department      # phòng ban
        self.base_salary = base_salary    # lương cơ bản

        # Trường phục vụ tính năng khóa tài khoản khi đăng nhập sai
        self.login_attempts = 0           # Số lần đăng nhập sai
        self.is_locked = False            # Trạng thái khóa tài khoản

    # Chuyển object -> dict để lưu vào JSON
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "base_salary": self.base_salary,
            "login_attempts": self.login_attempts,
            "is_locked": self.is_locked
        }

    # Chuyển dict -> object khi đọc từ JSON
    @staticmethod
    def from_dict(data: dict) -> "Employee":
        emp = Employee.__new__(Employee)
        emp.id = data["id"]
        emp.username = data["username"]
        emp.password_hash = data["password_hash"]
        emp.name = data["name"]
        emp.role = data["role"]
        emp.department = data["department"]
        emp.base_salary = data["base_salary"]
        emp.login_attempts = data.get("login_attempts", 0)
        emp.is_locked = data.get("is_locked", False)
        return emp

    # --- Getter / Setter ---
    def get_id(self): return self.id
    def get_username(self): return self.username
    def get_name(self): return self.name
    def get_role(self): return self.role
    def get_department(self): return self.department
    def get_base_salary(self): return self.base_salary

    def set_name(self, name): self.name = name
    def set_department(self, department): self.department = department
    def set_base_salary(self, salary): self.base_salary = salary
    def set_password_hash(self, ph): self.password_hash = ph
    
    # --- Phương thức hỗ trợ khóa/mở khóa tài khoản ---
    def reset_login_attempts(self):
        """Reset số lần đăng nhập sai về 0"""
        self.login_attempts = 0
    
    def unlock_account(self):
        """Mở khóa tài khoản"""
        self.is_locked = False
        self.login_attempts = 0
    
    def lock_account(self):
        """Khóa tài khoản"""
        self.is_locked = True