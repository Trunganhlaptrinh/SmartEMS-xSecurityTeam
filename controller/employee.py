# model/employee.py
# model: lưu trữ thông tin nhân viên (thuộc tính, constructor, getter/setter)
# tương tự Student.java trong bài cũ

class Employee:
    # biến class dùng để tự tăng ID (giống static int idCounter trong Java)
    _id_counter = 1

    def __init__(self, username: str, password_hash: str, name: str, role: str, department: str, base_salary: float):
        # gán id rồi tăng lên 1 (giống this.id = idCounter++ trong Java)
        self.id = Employee._id_counter
        Employee._id_counter += 1

        self.username    = username        # tài khoản đăng nhập
        self.password_hash = password_hash # mật khẩu đã hash
        self.name        = name            # tên hiển thị
        self.role        = role            # "admin" hoặc "employee"
        self.department  = department      # phòng ban
        self.base_salary = base_salary     # lương cơ bản

    # chuyển object → dict để lưu vào JSON (không có trong Java vì Java dùng DB)
    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "username":      self.username,
            "password_hash": self.password_hash,
            "name":          self.name,
            "role":          self.role,
            "department":    self.department,
            "base_salary":   self.base_salary
        }

    # chuyển dict → object khi đọc từ JSON (factory method, static)
    @staticmethod
    def from_dict(data: dict) -> "Employee":
        emp = Employee.__new__(Employee)  # tạo object rỗng, không gọi __init__
        emp.id            = data["id"]
        emp.username      = data["username"]
        emp.password_hash = data["password_hash"]
        emp.name          = data["name"]
        emp.role          = data["role"]
        emp.department    = data["department"]
        emp.base_salary   = data["base_salary"]
        return emp

    # --- getter / setter (giống Java) ---
    def get_id(self):           return self.id
    def get_username(self):     return self.username
    def get_name(self):         return self.name
    def get_role(self):         return self.role
    def get_department(self):   return self.department
    def get_base_salary(self):  return self.base_salary

    def set_name(self, name):               self.name = name
    def set_department(self, department):   self.department = department
    def set_base_salary(self, salary):      self.base_salary = salary
    def set_password_hash(self, ph):        self.password_hash = ph
