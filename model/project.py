# model/project.py
# Model: Quản lý dự án

from datetime import datetime

class Project:
    _id_counter = 1

    def __init__(self, name: str, description: str, owner_id: int, owner_name: str,
                 status: str = "active", members: list = None):
        self.id = Project._id_counter
        Project._id_counter += 1
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.status = status
        self.members = members or []
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "status": self.status,
            "members": self.members,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: dict) -> "Project":
        proj = Project.__new__(Project)
        proj.id = data["id"]
        proj.name = data["name"]
        proj.description = data.get("description", "")
        proj.owner_id = data["owner_id"]
        proj.owner_name = data["owner_name"]
        proj.status = data.get("status", "active")
        proj.members = data.get("members", [])
        proj.created_at = data.get("created_at", "")
        proj.updated_at = data.get("updated_at", "")
        return proj


class ProjectFile:
    _id_counter = 1

    def __init__(self, project_id: int, name: str, content: str, 
                 employee_id: int, employee_name: str, 
                 commit_id: int = None, commit_message: str = ""):
        self.id = ProjectFile._id_counter
        ProjectFile._id_counter += 1
        self.project_id = project_id
        self.name = name
        self.content = content
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.commit_id = commit_id
        self.commit_message = commit_message
        self.size = len(content) if content else 0
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "content": self.content,
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "commit_id": self.commit_id,
            "commit_message": self.commit_message,
            "size": self.size,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: dict) -> "ProjectFile":
        pf = ProjectFile.__new__(ProjectFile)
        pf.id = data["id"]
        pf.project_id = data["project_id"]
        pf.name = data["name"]
        pf.content = data.get("content", "")
        pf.employee_id = data["employee_id"]
        pf.employee_name = data["employee_name"]
        pf.commit_id = data.get("commit_id")
        pf.commit_message = data.get("commit_message", "")
        pf.size = data.get("size", 0)
        pf.created_at = data.get("created_at", "")
        pf.updated_at = data.get("updated_at", "")
        return pf


class Commit:
    _id_counter = 1

    def __init__(self, project_id: int, employee_id: int, employee_name: str,
                 message: str, files: list = None):
        self.id = Commit._id_counter
        Commit._id_counter += 1
        self.project_id = project_id
        self.employee_id = employee_id
        self.employee_name = employee_name
        self.message = message
        self.files = files or []
        self.status = "pending"
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = self.created_at
        self.approved_by = None
        self.approved_at = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "message": self.message,
            "files": self.files,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at
        }

    @staticmethod
    def from_dict(data: dict) -> "Commit":
        commit = Commit.__new__(Commit)
        commit.id = data["id"]
        commit.project_id = data["project_id"]
        commit.employee_id = data["employee_id"]
        commit.employee_name = data["employee_name"]
        commit.message = data["message"]
        commit.files = data.get("files", [])
        commit.status = data.get("status", "pending")
        commit.created_at = data.get("created_at", "")
        commit.updated_at = data.get("updated_at", "")
        commit.approved_by = data.get("approved_by")
        commit.approved_at = data.get("approved_at")
        return commit