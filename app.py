# app.py - ĐÃ FIX LỖ HỔNG CORS
from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from controller.auth_controller import auth_bp
from controller.attendance_controller import attendance_bp
from controller.leave_controller import leave_bp
from controller.salary_controller import salary_bp
from controller.shop_controller import shop_bp
from controller.notification_controller import notification_bp
from controller.project_controller import project_bp
from controller.otp_controller import otp_bp
from controller.task_controller import task_bp

from model.employee import Employee
from model.attendance import Attendance
from model.leave import Leave
from model.salary import Salary
from model.shop import ShopItem, ShopTransaction
from model.notification import Notification
from model.project import Project, Commit, ProjectFile
from model.otp import OTP
from model.task import Task

from util.file_helper import FileHelper
from util.auth_helper import AuthHelper


app = Flask(__name__)
app.secret_key = "employee_mgmt_secret_2025"

VIEW_DIR = os.path.join(os.path.dirname(__file__), "view")

ALLOWED_ORIGINS = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]

CORS(
    app,
    origins=ALLOWED_ORIGINS,
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ]
)

print(
    f"[SECURITY] CORS configured - Allowed origins: "
    f"{ALLOWED_ORIGINS}"
)


@app.route("/")
def index():
    return send_from_directory(VIEW_DIR, "index.html")


@app.route("/<path:filename>")
def serve_view(filename):
    return send_from_directory(VIEW_DIR, filename)


# ==========================
# REGISTER BLUEPRINTS
# ==========================
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(leave_bp, url_prefix="/api/leave")
app.register_blueprint(salary_bp, url_prefix="/api/salary")
app.register_blueprint(shop_bp, url_prefix="/api/shop")
app.register_blueprint(notification_bp, url_prefix="/api/notifications")
app.register_blueprint(project_bp, url_prefix="/api/projects")
app.register_blueprint(otp_bp, url_prefix="/api/otp")
app.register_blueprint(task_bp, url_prefix="/api/tasks")


def sync_id_counters():
    Employee._id_counter = FileHelper.get_max_id("employees") + 1
    Attendance._id_counter = FileHelper.get_max_id("attendance") + 1
    Leave._id_counter = FileHelper.get_max_id("leaves") + 1
    Salary._id_counter = FileHelper.get_max_id("salaries") + 1

    ShopItem._id_counter = FileHelper.get_max_id("shop_items") + 1
    ShopTransaction._id_counter = (
        FileHelper.get_max_id("shop_transactions") + 1
    )

    Notification._id_counter = (
        FileHelper.get_max_id("notifications") + 1
    )

    Project._id_counter = FileHelper.get_max_id("projects") + 1
    Commit._id_counter = FileHelper.get_max_id("commits") + 1
    ProjectFile._id_counter = (
        FileHelper.get_max_id("project_files") + 1
    )

    OTP._id_counter = FileHelper.get_max_id("otp_codes") + 1
    Task._id_counter = FileHelper.get_max_id("tasks") + 1


def create_default_admin():
    employees = FileHelper.read_all("employees")

    if not employees:
        admin = Employee(
            username="admin",
            password_hash=AuthHelper.hash_password("admin123"),
            name="Administrator",
            role="admin",
            department="Management",
            base_salary=0
        )

        FileHelper.append_item(
            "employees",
            admin.to_dict()
        )

        print(
            "Đã tạo tài khoản admin mặc định:"
            " admin / admin123"
        )


if __name__ == "__main__":
    sync_id_counters()
    create_default_admin()

    print("🚀 Server Task Management đã sẵn sàng!")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )