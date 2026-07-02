# model/notification.py
# Model: Quản lý thông báo

from datetime import datetime

class Notification:
    _id_counter = 1

    def __init__(self, title: str, content: str, author_id: int, author_name: str, 
                 notification_type: str = "general", priority: str = "normal"):
        """
        notification_type: general | meeting | holiday | urgent
        priority: normal | high | urgent
        """
        self.id = Notification._id_counter
        Notification._id_counter += 1
        self.title = title
        self.content = content
        self.author_id = author_id
        self.author_name = author_name
        self.notification_type = notification_type
        self.priority = priority
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at
        self.status = "active"  # active | archived

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "notification_type": self.notification_type,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status
        }

    @staticmethod
    def from_dict(data: dict) -> "Notification":
        noti = Notification.__new__(Notification)
        noti.id = data["id"]
        noti.title = data["title"]
        noti.content = data["content"]
        noti.author_id = data["author_id"]
        noti.author_name = data["author_name"]
        noti.notification_type = data.get("notification_type", "general")
        noti.priority = data.get("priority", "normal")
        noti.created_at = data.get("created_at", "")
        noti.updated_at = data.get("updated_at", "")
        noti.status = data.get("status", "active")
        return noti