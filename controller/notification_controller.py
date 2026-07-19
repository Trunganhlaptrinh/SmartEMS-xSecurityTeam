# controller/notification_controller.py
# Controller: Quản lý thông báo

from flask import Blueprint, request, jsonify, session
from model.notification import Notification
from util.file_helper import FileHelper
from datetime import datetime

notification_bp = Blueprint("notification", __name__)


# ========================
# LẤY SỐ LƯỢNG THÔNG BÁO
# GET /api/notifications/count
# PHẢI ĐẶT TRƯỚC /<int:noti_id> để Flask không match "count" như một số nguyên
# ========================
@notification_bp.route("/count", methods=["GET"])
def get_notification_count():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    notifications = FileHelper.read_all("notifications")
    active = [n for n in notifications if n.get("status") == "active"]

    return jsonify({
        "success": True,
        "data": {
            "total": len(active),
            "by_type": {
                "general": sum(1 for n in active if n.get("notification_type") == "general"),
                "meeting":  sum(1 for n in active if n.get("notification_type") == "meeting"),
                "holiday":  sum(1 for n in active if n.get("notification_type") == "holiday"),
                "urgent":   sum(1 for n in active if n.get("notification_type") == "urgent"),
            }
        }
    })


# ========================
# LẤY DANH SÁCH THÔNG BÁO
# GET /api/notifications?type=&priority=
# ========================
@notification_bp.route("", methods=["GET"])
def get_notifications():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    notifications = FileHelper.read_all("notifications")

    # chỉ lấy active (đã đăng, chưa xóa)
    notifications = [n for n in notifications if n.get("status") == "active"]

    # lọc theo type nếu có
    noti_type = request.args.get("type")
    if noti_type:
        notifications = [n for n in notifications if n.get("notification_type") == noti_type]

    # lọc theo priority nếu có
    priority = request.args.get("priority")
    if priority:
        notifications = [n for n in notifications if n.get("priority") == priority]

    # sắp xếp mới nhất lên đầu
    notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return jsonify({"success": True, "data": notifications})


# ========================
# LẤY 1 THÔNG BÁO
# GET /api/notifications/<id>
# ========================
@notification_bp.route("/<int:noti_id>", methods=["GET"])
def get_notification(noti_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    notifications = FileHelper.read_all("notifications")
    noti = next((n for n in notifications if n["id"] == noti_id), None)

    if not noti:
        return jsonify({"success": False, "message": "Không tìm thấy thông báo"}), 404

    return jsonify({"success": True, "data": noti})


# ========================
# TẠO THÔNG BÁO (chỉ admin)
# POST /api/notifications
# ========================
@notification_bp.route("", methods=["POST"])
def create_notification():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    title   = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    noti_type = data.get("notification_type", "general")
    priority  = data.get("priority", "normal")

    if not title:
        return jsonify({"success": False, "message": "Tiêu đề không được để trống"}), 400
    if not content:
        return jsonify({"success": False, "message": "Nội dung không được để trống"}), 400
    if noti_type not in ["general", "meeting", "holiday", "urgent"]:
        return jsonify({"success": False, "message": "Loại thông báo không hợp lệ"}), 400
    if priority not in ["normal", "high", "urgent"]:
        return jsonify({"success": False, "message": "Mức độ ưu tiên không hợp lệ"}), 400

    # lấy tên admin đang đăng nhập
    employees   = FileHelper.read_all("employees")
    author      = next((e for e in employees if e["id"] == session["employee_id"]), None)
    author_name = author["name"] if author else "Administrator"

    noti = Notification(
        title=title,
        content=content,
        author_id=session["employee_id"],
        author_name=author_name,
        notification_type=noti_type,
        priority=priority
    )

    FileHelper.append_item("notifications", noti.to_dict())
    return jsonify({"success": True, "message": "Đăng thông báo thành công", "id": noti.id}), 201


# ========================
# CẬP NHẬT THÔNG BÁO (chỉ admin)
# PUT /api/notifications/<id>
# ========================
@notification_bp.route("/<int:noti_id>", methods=["PUT"])
def update_notification(noti_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data      = request.get_json()
    title     = (data.get("title") or "").strip()
    content   = (data.get("content") or "").strip()
    noti_type = data.get("notification_type", "general")
    priority  = data.get("priority", "normal")

    if not title:
        return jsonify({"success": False, "message": "Tiêu đề không được để trống"}), 400
    if not content:
        return jsonify({"success": False, "message": "Nội dung không được để trống"}), 400

    notifications = FileHelper.read_all("notifications")
    for i, n in enumerate(notifications):
        if n["id"] == noti_id:
            notifications[i]["title"]             = title
            notifications[i]["content"]           = content
            notifications[i]["notification_type"] = noti_type
            notifications[i]["priority"]          = priority
            notifications[i]["updated_at"]        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            FileHelper.write_all("notifications", notifications)
            return jsonify({"success": True, "message": "Cập nhật thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy thông báo"}), 404


# ========================
# XÓA THÔNG BÁO (chỉ admin) — soft delete: chuyển sang archived
# DELETE /api/notifications/<id>
# ========================
@notification_bp.route("/<int:noti_id>", methods=["DELETE"])
def delete_notification(noti_id):
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    notifications = FileHelper.read_all("notifications")
    for i, n in enumerate(notifications):
        if n["id"] == noti_id:
            notifications[i]["status"]     = "archived"
            notifications[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            FileHelper.write_all("notifications", notifications)
            return jsonify({"success": True, "message": "Đã xóa thông báo"})

    return jsonify({"success": False, "message": "Không tìm thấy thông báo"}), 404