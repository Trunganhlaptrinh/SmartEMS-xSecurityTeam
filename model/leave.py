# model/leave.py
# model: lưu thông tin đơn xin nghỉ phép của nhân viên

class Leave:
    _id_counter = 1

    def __init__(self, employee_id: int, from_date: str, to_date: str, reason: str):
        self.id          = Leave._id_counter
        Leave._id_counter += 1

        self.employee_id = employee_id  # ID nhân viên
        self.from_date   = from_date    # ngày bắt đầu nghỉ "YYYY-MM-DD"
        self.to_date     = to_date      # ngày kết thúc nghỉ "YYYY-MM-DD"
        self.reason      = reason       # lý do
        self.status      = "pending"    # "pending" | "approved" | "rejected"

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "employee_id": self.employee_id,
            "from_date":   self.from_date,
            "to_date":     self.to_date,
            "reason":      self.reason,
            "status":      self.status
        }

    @staticmethod
    def from_dict(data: dict) -> "Leave":
        lv = Leave.__new__(Leave)
        lv.id          = data["id"]
        lv.employee_id = data["employee_id"]
        lv.from_date   = data["from_date"]
        lv.to_date     = data["to_date"]
        lv.reason      = data["reason"]
        lv.status      = data["status"]
        return lv

    # getter / setter
    def get_id(self):           return self.id
    def get_employee_id(self):  return self.employee_id
    def get_from_date(self):    return self.from_date
    def get_to_date(self):      return self.to_date
    def get_reason(self):       return self.reason
    def get_status(self):       return self.status

    def set_status(self, status): self.status = status
    def set_reason(self, reason): self.reason = reason
