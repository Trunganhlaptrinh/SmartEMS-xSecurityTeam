# controller/task_controller.py
from flask import Blueprint, request, jsonify, session
from model.task import Task
from util.file_helper import FileHelper
from util.validation import Validation
from datetime import datetime

task_bp = Blueprint("task", __name__)

# GET tasks
@task_bp.route("", methods=["GET"])
def get_tasks():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        tasks = FileHelper.read_all("tasks")
        
        # User chỉ xem task của mình
        if session.get("role") != "admin":
            tasks = [t for t in tasks if t.get("assignee_id") == session["employee_id"]]
        
        status = request.args.get("status")
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        
        tasks.sort(key=lambda x: x.get("due_date") or "9999", reverse=False)
        return jsonify({"success": True, "data": tasks})
    except Exception as e:
        print("Lỗi get_tasks:", str(e))
        return jsonify({"success": False, "message": "Lỗi server"}), 500


# CREATE - CHỈ ADMIN
@task_bp.route("", methods=["POST"])
def create_task():
    if "employee_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ admin mới được tạo task"}), 403

    try:
        data = request.get_json()
        title = Validation.check_not_empty(data.get("title", ""), "Tiêu đề")
        
        employees = FileHelper.read_all("employees")
        assignee = next((e for e in employees if e["id"] == int(data.get("assignee_id", 0))), None)
        if not assignee:
            return jsonify({"success": False, "message": "Nhân viên không tồn tại"}), 400

        creator = next((e for e in employees if e["id"] == session["employee_id"]), None)

        task = Task(
            title=title,
            description=data.get("description", ""),
            assignee_id=assignee["id"],
            assignee_name=assignee["name"],
            creator_id=session["employee_id"],
            creator_name=creator["name"] if creator else "Admin",
            due_date=data.get("due_date"),
            priority=data.get("priority", "medium"),
            status="todo"
        )
        
        FileHelper.append_item("tasks", task.to_dict())
        return jsonify({"success": True, "message": "Tạo nhiệm vụ thành công", "id": task.id}), 201
    except Exception as e:
        print("Lỗi create_task:", str(e))
        return jsonify({"success": False, "message": "Lỗi server"}), 500


# UPDATE - ADMIN hoặc người được giao task (chỉ cập nhật status + một số field)
@task_bp.route("/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        data = request.get_json()
        tasks = FileHelper.read_all("tasks")
        task_dict = next((t for t in tasks if t["id"] == task_id), None)
        if not task_dict:
            return jsonify({"success": False, "message": "Không tìm thấy task"}), 404

        # Quyền: Admin hoặc người được giao
        if session.get("role") != "admin" and task_dict.get("assignee_id") != session["employee_id"]:
            return jsonify({"success": False, "message": "Không có quyền cập nhật task này"}), 403

        # User chỉ được cập nhật status
        if session.get("role") != "admin":
            if "status" in data:
                task_dict["status"] = data["status"]
            # Không cho user sửa tiêu đề, người thực hiện...
        else:
            # Admin được sửa full
            if "title" in data:
                task_dict["title"] = data["title"]
            if "description" in data:
                task_dict["description"] = data["description"]
            if "assignee_id" in data:
                task_dict["assignee_id"] = int(data["assignee_id"])
            if "status" in data:
                task_dict["status"] = data["status"]
            if "priority" in data:
                task_dict["priority"] = data["priority"]
            if "due_date" in data:
                task_dict["due_date"] = data["due_date"]

        task_dict["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        FileHelper.update_item("tasks", task_id, task_dict)
        return jsonify({"success": True, "message": "Cập nhật task thành công"})
    except Exception as e:
        print("Lỗi update_task:", str(e))
        return jsonify({"success": False, "message": "Lỗi server"}), 500