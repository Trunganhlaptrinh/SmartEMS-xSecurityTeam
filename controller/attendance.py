# model/attendance.py
# model: lưu thông tin điểm danh từng ngày của nhân viên

class Attendance:
    _id_counter = 1

    def __init__(self, employee_id: int, date: str, status: str, note: str = ""):
        self.id          = Attendance._id_counter
        Attendance._id_counter += 1

        self.employee_id = employee_id  # ID nhân viên
        self.date        = date          # "YYYY-MM-DD"
        self.status      = status        # "present" | "absent" | "late"
        self.note        = note          # ghi chú tùy chọn

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "employee_id": self.employee_id,
            "date":        self.date,
            "status":      self.status,
            "note":        self.note
        }

    @staticmethod
    def from_dict(data: dict) -> "Attendance":
        att = Attendance.__new__(Attendance)
        att.id          = data["id"]
        att.employee_id = data["employee_id"]
        att.date        = data["date"]
        att.status      = data["status"]
        att.note        = data.get("note", "")
        return att

    # getter / setter
    def get_id(self):           return self.id
    def get_employee_id(self):  return self.employee_id
    def get_date(self):         return self.date
    def get_status(self):       return self.status
    def get_note(self):         return self.note

    def set_status(self, status): self.status = status
    def set_note(self, note):     self.note = note
