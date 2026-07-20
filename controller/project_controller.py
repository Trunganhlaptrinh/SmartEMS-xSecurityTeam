# controller/project_controller.py
# Controller: Quản lý dự án

from flask import Blueprint, request, jsonify, session, send_file
from model.project import Project, ProjectFile, Commit
from util.file_helper import FileHelper
from util.validation import Validation
from datetime import datetime
import base64
import io
import zipfile

project_bp = Blueprint("project", __name__)


# ========================
# QUẢN LÝ DỰ ÁN
# ========================

@project_bp.route("", methods=["GET"])
def get_projects():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        projects = FileHelper.read_all("projects")
        
        if session.get("role") != "admin":
            projects = [p for p in projects if 
                       session["employee_id"] in p.get("members", []) or 
                       p.get("owner_id") == session["employee_id"]]
        
        status = request.args.get("status")
        if status:
            projects = [p for p in projects if p.get("status") == status]
        
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jsonify({"success": True, "data": projects})
    except Exception as e:
        print("Lỗi get_projects:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        projects = FileHelper.read_all("projects")
        project = next((p for p in projects if p["id"] == project_id), None)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404
        
        if session.get("role") != "admin":
            if (session["employee_id"] not in project.get("members", []) and 
                project.get("owner_id") != session["employee_id"]):
                return jsonify({"success": False, "message": "Không có quyền truy cập"}), 403
        
        return jsonify({"success": True, "data": project})
    except Exception as e:
        print("Lỗi get_project:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("", methods=["POST"])
def create_project():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"success": False, "message": "Tên dự án không được để trống"}), 400

        employees = FileHelper.read_all("employees")
        author = next((e for e in employees if e["id"] == session["employee_id"]), None)
        author_name = author["name"] if author else "Administrator"

        project = Project(
            name=name,
            description=data.get("description", "").strip(),
            owner_id=session["employee_id"],
            owner_name=author_name,
            status=data.get("status", "active"),
            members=data.get("members", [])
        )
        
        FileHelper.append_item("projects", project.to_dict())
        return jsonify({"success": True, "message": "Tạo dự án thành công", "id": project.id}), 201
    except Exception as e:
        print("Lỗi create_project:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"success": False, "message": "Tên dự án không được để trống"}), 400

        projects = FileHelper.read_all("projects")
        for i, p in enumerate(projects):
            if p["id"] == project_id:
                projects[i]["name"] = name
                projects[i]["description"] = data.get("description", "").strip()
                projects[i]["status"] = data.get("status", "active")
                projects[i]["members"] = data.get("members", [])
                projects[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                FileHelper.write_all("projects", projects)
                return jsonify({"success": True, "message": "Cập nhật thành công"})

        return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404
    except Exception as e:
        print("Lỗi update_project:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    try:
        ok = FileHelper.delete_item("projects", project_id)
        if not ok:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404
        return jsonify({"success": True, "message": "Đã xóa dự án"})
    except Exception as e:
        print("Lỗi delete_project:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# QUẢN LÝ FILE DỰ ÁN
# ========================

@project_bp.route("/<int:project_id>/files", methods=["GET"])
def get_project_files(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        projects = FileHelper.read_all("projects")
        project = next((p for p in projects if p["id"] == project_id), None)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404

        files = FileHelper.read_all("project_files")
        files = [f for f in files if f["project_id"] == project_id]
        
        for f in files:
            if "content" in f:
                f["content"] = "[HIDDEN]"
        
        files.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jsonify({"success": True, "data": files})
    except Exception as e:
        print("Lỗi get_project_files:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>/files/<int:file_id>/download", methods=["GET"])
def download_file(project_id, file_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        files = FileHelper.read_all("project_files")
        file_data = next((f for f in files if f["id"] == file_id and f["project_id"] == project_id), None)
        
        if not file_data:
            return jsonify({"success": False, "message": "Không tìm thấy file"}), 404

        content = file_data.get("content", "")
        if not content:
            return jsonify({"success": False, "message": "File trống"}), 400

        try:
            if content.startswith('data:'):
                content = content.split(',', 1)[1] if ',' in content else content
            file_bytes = base64.b64decode(content)
        except Exception as e:
            return jsonify({"success": False, "message": "Lỗi giải mã file"}), 500

        return send_file(
            io.BytesIO(file_bytes),
            as_attachment=True,
            download_name=file_data["name"],
            mimetype="application/octet-stream"
        )
    except Exception as e:
        print("Lỗi download_file:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# TẢI TẤT CẢ FILE DỰ ÁN (ZIP)
# ========================
@project_bp.route("/<int:project_id>/files/download-all", methods=["GET"])
def download_all_files(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        projects = FileHelper.read_all("projects")
        project = next((p for p in projects if p["id"] == project_id), None)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404

        if session.get("role") != "admin":
            if (session["employee_id"] not in project.get("members", []) and 
                project.get("owner_id") != session["employee_id"]):
                return jsonify({"success": False, "message": "Không có quyền truy cập"}), 403

        files = FileHelper.read_all("project_files")
        project_files = [f for f in files if f["project_id"] == project_id]
        
        if not project_files:
            return jsonify({"success": False, "message": "Dự án chưa có file nào"}), 404

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_data in project_files:
                content = file_data.get("content", "")
                if not content:
                    continue
                
                try:
                    if content.startswith('data:'):
                        content = content.split(',', 1)[1] if ',' in content else content
                    file_bytes = base64.b64decode(content)
                except Exception as e:
                    print(f"Lỗi giải mã file {file_data.get('name')}: {e}")
                    continue
                
                zip_file.writestr(file_data.get("name", "unknown"), file_bytes)

        zip_buffer.seek(0)
        project_name = project.get("name", "project")
        filename = f"{project_name}_files.zip"
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/zip"
        )
    except Exception as e:
        print("Lỗi download_all_files:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


# ========================
# QUẢN LÝ COMMIT
# ========================

@project_bp.route("/<int:project_id>/commits", methods=["GET"])
def get_commits(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        projects = FileHelper.read_all("projects")
        project = next((p for p in projects if p["id"] == project_id), None)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404

        if session.get("role") != "admin":
            if (session["employee_id"] not in project.get("members", []) and 
                project.get("owner_id") != session["employee_id"]):
                return jsonify({"success": False, "message": "Không có quyền"}), 403

        commits = FileHelper.read_all("commits")
        commits = [c for c in commits if c["project_id"] == project_id]
        
        status = request.args.get("status")
        if status:
            commits = [c for c in commits if c.get("status") == status]
        
        commits.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        employees = FileHelper.read_all("employees")
        emp_map = {e["id"]: e["name"] for e in employees}
        for c in commits:
            c["employee_name"] = emp_map.get(c["employee_id"], f"ID {c['employee_id']}")
        
        return jsonify({"success": True, "data": commits})
    except Exception as e:
        print("Lỗi get_commits:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>/commits", methods=["POST"])
def create_commit(project_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        projects = FileHelper.read_all("projects")
        project = next((p for p in projects if p["id"] == project_id), None)
        if not project:
            return jsonify({"success": False, "message": "Không tìm thấy dự án"}), 404

        if session["employee_id"] not in project.get("members", []) and project.get("owner_id") != session["employee_id"]:
            return jsonify({"success": False, "message": "Bạn không phải thành viên của dự án này"}), 403

        data = request.get_json()
        message = data.get("message", "").strip()
        files_data = data.get("files", [])
        
        if not message:
            return jsonify({"success": False, "message": "Nội dung commit không được để trống"}), 400

        employees = FileHelper.read_all("employees")
        emp = next((e for e in employees if e["id"] == session["employee_id"]), None)
        emp_name = emp["name"] if emp else f"ID {session['employee_id']}"

        commit = Commit(
            project_id=project_id,
            employee_id=session["employee_id"],
            employee_name=emp_name,
            message=message,
            files=[f["name"] for f in files_data]
        )
        FileHelper.append_item("commits", commit.to_dict())

        for file_data in files_data:
            project_file = ProjectFile(
                project_id=project_id,
                name=file_data["name"],
                content=file_data["content"],
                employee_id=session["employee_id"],
                employee_name=emp_name,
                commit_id=commit.id,
                commit_message=message
            )
            FileHelper.append_item("project_files", project_file.to_dict())

        return jsonify({"success": True, "message": "Gửi commit thành công, chờ admin duyệt", "id": commit.id}), 201
    except Exception as e:
        print("Lỗi create_commit:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>/commits/<int:commit_id>", methods=["PUT"])
def update_commit(project_id, commit_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    try:
        data = request.get_json()
        status = data.get("status", "").strip()
        
        if status not in ["approved", "rejected"]:
            return jsonify({"success": False, "message": "Trạng thái phải là approved hoặc rejected"}), 400

        commits = FileHelper.read_all("commits")
        for i, c in enumerate(commits):
            if c["id"] == commit_id and c["project_id"] == project_id:
                if c["status"] != "pending":
                    return jsonify({"success": False, "message": f"Commit đã được {c['status']}"}), 400
                
                commits[i]["status"] = status
                commits[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commits[i]["approved_by"] = session["employee_id"]
                commits[i]["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                FileHelper.write_all("commits", commits)
                
                msg = "Duyệt thành công" if status == "approved" else "Từ chối thành công"
                return jsonify({"success": True, "message": msg})

        return jsonify({"success": False, "message": "Không tìm thấy commit"}), 404
    except Exception as e:
        print("Lỗi update_commit:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500


@project_bp.route("/<int:project_id>/commits/<int:commit_id>", methods=["DELETE"])
def delete_commit(project_id, commit_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        commits = FileHelper.read_all("commits")
        commit = next((c for c in commits if c["id"] == commit_id and c["project_id"] == project_id), None)
        
        if not commit:
            return jsonify({"success": False, "message": "Không tìm thấy commit"}), 404

        if session.get("role") != "admin" and commit["employee_id"] != session["employee_id"]:
            return jsonify({"success": False, "message": "Không có quyền xóa"}), 403

        files = FileHelper.read_all("project_files")
        files = [f for f in files if not (f["commit_id"] == commit_id and f["project_id"] == project_id)]
        FileHelper.write_all("project_files", files)

        ok = FileHelper.delete_item("commits", commit_id)
        if not ok:
            return jsonify({"success": False, "message": "Không tìm thấy commit"}), 404

        return jsonify({"success": True, "message": "Đã xóa commit"})
    except Exception as e:
        print("Lỗi delete_commit:", str(e))
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)}), 500