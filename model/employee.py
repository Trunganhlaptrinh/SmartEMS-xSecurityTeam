# model/employee.py
# model: lưu trữ thông tin nhân viên

class Employee:
    _id_counter = 1

    def __init__(self, username: str, password_hash: str, name: str, role: str, department: str, base_salary: float):
        self.id = Employee._id_counter
        Employee._id_counter += 1

        self.username = username
        self.password_hash = password_hash
        self.name = name
        self.role = role
        self.department = department
        self.base_salary = base_salary
        # Thêm trường mới cho khóa tài khoản
        self.login_attempts = 0          # Số lần đăng nhập sai
        self.is_locked = False           # Trạng thái khóa tài khoản

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
    
    # Thêm phương thức mới
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