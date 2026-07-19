# model/task.py
# Model: Quản lý nhiệm vụ / Task Management

from datetime import datetime

class Task:
    _id_counter = 1

    def __init__(self, title: str, description: str, assignee_id: int, assignee_name: str,
                 creator_id: int, creator_name: str, due_date: str = None,
                 priority: str = "medium", status: str = "todo"):
        self.id = Task._id_counter
        Task._id_counter += 1
        self.title = title
        self.description = description
        self.assignee_id = assignee_id
        self.assignee_name = assignee_name
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.status = status  # todo, inprogress, done
        self.priority = priority  # low, medium, high
        self.due_date = due_date
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee_name,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        task = Task.__new__(Task)
        task.id = data["id"]
        task.title = data["title"]
        task.description = data.get("description", "")
        task.assignee_id = data["assignee_id"]
        task.assignee_name = data["assignee_name"]
        task.creator_id = data["creator_id"]
        task.creator_name = data["creator_name"]
        task.status = data.get("status", "todo")
        task.priority = data.get("priority", "medium")
        task.due_date = data.get("due_date")
        task.created_at = data.get("created_at", "")
        task.updated_at = data.get("updated_at", "")
        return task