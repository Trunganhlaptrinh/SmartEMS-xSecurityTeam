# model/contract.py
# Model: Hợp đồng dự án (Project Contract)
# Chỉ admin và những người được admin chỉ định (allowed_viewers) mới xem được

from datetime import datetime


class Contract:
    _id_counter = 1

    def __init__(self, project_id: int, title: str, description: str,
                 created_by: int, created_by_name: str,
                 file_name: str = "", file_content: str = "",
                 allowed_viewers: list = None):
        self.id = Contract._id_counter
        Contract._id_counter += 1
        self.project_id = project_id
        self.title = title
        self.description = description
        self.created_by = created_by
        self.created_by_name = created_by_name
        self.file_name = file_name
        self.file_content = file_content          # base64, có thể rỗng nếu chỉ có mô tả
        self.file_size = len(file_content) if file_content else 0
        # danh sách employee_id được admin chỉ định cho xem hợp đồng này
        self.allowed_viewers = allowed_viewers or []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "file_name": self.file_name,
            "file_content": self.file_content,
            "file_size": self.file_size,
            "allowed_viewers": self.allowed_viewers,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    # dùng khi trả về danh sách / chi tiết cho người xem thường
    # (không kèm nội dung file base64 để tránh tải nặng danh sách)
    def to_dict_summary(self) -> dict:
        d = self.to_dict()
        d.pop("file_content", None)
        return d

    @staticmethod
    def from_dict(data: dict) -> "Contract":
        c = Contract.__new__(Contract)
        c.id = data["id"]
        c.project_id = data["project_id"]
        c.title = data["title"]
        c.description = data.get("description", "")
        c.created_by = data["created_by"]
        c.created_by_name = data.get("created_by_name", "")
        c.file_name = data.get("file_name", "")
        c.file_content = data.get("file_content", "")
        c.file_size = data.get("file_size", 0)
        c.allowed_viewers = data.get("allowed_viewers", [])
        c.created_at = data.get("created_at", "")
        c.updated_at = data.get("updated_at", "")
        return c