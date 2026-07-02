# model/salary.py
# model: lưu thông tin bảng lương tháng của nhân viên

class Salary:
    _id_counter = 1

    def __init__(self, employee_id: int, month: str, base: float, bonus: float, deduction: float):
        self.id          = Salary._id_counter
        Salary._id_counter += 1

        self.employee_id = employee_id  # ID nhân viên
        self.month       = month         # "YYYY-MM" ví dụ "2025-06"
        self.base        = base          # lương cơ bản
        self.bonus       = bonus         # thưởng
        self.deduction   = deduction     # khấu trừ (nghỉ không phép, đi muộn...)
        self.total       = base + bonus - deduction  # tổng lương thực nhận

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "employee_id": self.employee_id,
            "month":       self.month,
            "base":        self.base,
            "bonus":       self.bonus,
            "deduction":   self.deduction,
            "total":       self.total
        }

    @staticmethod
    def from_dict(data: dict) -> "Salary":
        sal = Salary.__new__(Salary)
        sal.id          = data["id"]
        sal.employee_id = data["employee_id"]
        sal.month       = data["month"]
        sal.base        = data["base"]
        sal.bonus       = data["bonus"]
        sal.deduction   = data["deduction"]
        sal.total       = data["total"]
        return sal

    # getter / setter
    def get_id(self):           return self.id
    def get_employee_id(self):  return self.employee_id
    def get_month(self):        return self.month
    def get_total(self):        return self.total

    def set_bonus(self, bonus):           self.bonus = bonus;     self._recalc()
    def set_deduction(self, deduction):   self.deduction = deduction; self._recalc()

    # tính lại tổng sau khi cập nhật bonus/deduction
    def _recalc(self):
        self.total = self.base + self.bonus - self.deduction
