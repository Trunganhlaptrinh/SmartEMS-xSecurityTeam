# app.py
# SmartEMS Main Application - Khong can flask_session

from flask import Flask, send_from_directory, jsonify, session
from flask_cors import CORS
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# =====================================
# TAI BIEN MOI TRUONG
# =====================================
load_dotenv()

# =====================================
# CAU HINH LOGGING
# =====================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =====================================
# NHAP CAC CONTROLLER
# =====================================
from controller.auth_controller import auth_bp
from controller.attendance_controller import attendance_bp
from controller.leave_controller import leave_bp
from controller.salary_controller import salary_bp
from controller.shop_controller import shop_bp
from controller.notification_controller import notification_bp
from controller.project_controller import project_bp
from controller.contract_controller import contract_bp, contract_list_bp
from controller.otp_controller import otp_bp
from controller.task_controller import task_bp
from controller.dashboard_controller import dashboard_bp
from controller.ai_controller import ai_bp

# =====================================
# NHAP CAC MODEL
# =====================================
from model.employee import Employee
from model.attendance import Attendance
from model.leave import Leave
from model.salary import Salary
from model.shop import ShopItem, ShopTransaction
from model.notification import Notification
from model.project import Project, Commit, ProjectFile
from model.contract import Contract
from model.otp import OTP
from model.task import Task

# =====================================
# NHAP CAC UTILITY
# =====================================
from util.file_helper import FileHelper
from util.auth_helper import AuthHelper

# =====================================
# KHOI TAO UNG DUNG FLASK
# =====================================
app = Flask(__name__)

# =====================================
# CAU HINH UNG DUNG
# =====================================
class Config:
    """Cau hinh ung dung"""

    # Khoa bi mat - uu tien lay tu bien moi truong SECRET_KEY (khi deploy that),
    # neu chua set thi tam dung gia tri mac dinh + canh bao de khong quen doi.
    SECRET_KEY = os.environ.get("SECRET_KEY", "employee_mgmt_secret_2025")

    # CORS
    CORS_ORIGINS = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    # Duong dan
    VIEW_DIR = os.path.join(os.path.dirname(__file__), "view")
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

    # Che do debug
    DEBUG = os.environ.get("FLASK_ENV") != "production"

app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

if not os.environ.get("SECRET_KEY"):
    print(
        "[SECURITY] \u26a0\ufe0f  Chua dat bien moi truong SECRET_KEY, dang dung gia tri mac dinh "
        "(KHONG an toan khi chay that ngoai internet). Nen set: export SECRET_KEY=\"...\""
    )

# =====================================
# THIET LAP CORS
# =====================================
CORS(
    app,
    origins=Config.CORS_ORIGINS,
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
    expose_headers=["Content-Disposition"]
)

logger.info("Da cau hinh CORS. Cac nguon duoc phep: %s", Config.CORS_ORIGINS)

# =====================================
# DUONG DAN - PHUC VU VIEW
# =====================================
@app.route("/")
def index():
    """Trang dang nhap"""
    return send_from_directory(Config.VIEW_DIR, "index.html")

@app.route("/<path:filename>")
def serve_view(filename):
    """Phuc vu cac file tinh trong thu muc view"""

    # Ngan chan tan cong duyet thu muc
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid path"}), 400

    # Chi cho phep cac loai file nhat dinh
    allowed_extensions = {
        '.html', '.css', '.js', '.png', '.jpg', '.jpeg',
        '.gif', '.ico', '.svg', '.json'
    }
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in allowed_extensions:
        return jsonify({"error": "File type not allowed"}), 403

    return send_from_directory(Config.VIEW_DIR, filename)

# =====================================
# DUONG DAN - KIEM TRA TRANG THAI API
# =====================================
@app.route("/api/status", methods=["GET"])
def api_status():
    """Kiem tra trang thai API"""
    return jsonify({
        "success": True,
        "status": "running",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("FLASK_ENV", "development")
    })

# =====================================
# DANG KY CAC BLUEPRINT
# =====================================
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(leave_bp, url_prefix="/api/leave")
app.register_blueprint(salary_bp, url_prefix="/api/salary")
app.register_blueprint(shop_bp, url_prefix="/api/shop")
app.register_blueprint(notification_bp, url_prefix="/api/notifications")
app.register_blueprint(project_bp, url_prefix="/api/projects")
app.register_blueprint(otp_bp, url_prefix="/api/otp")
app.register_blueprint(contract_bp, url_prefix="/api/projects")
app.register_blueprint(contract_list_bp, url_prefix="/api/contracts")
app.register_blueprint(task_bp, url_prefix="/api/tasks")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(ai_bp, url_prefix="/api/ai")

logger.info("Da dang ky tat ca cac blueprint")

# =====================================
# XU LY LOI
# =====================================
@app.errorhandler(404)
def not_found(error):
    """Loi 404 - Khong tim thay tai nguyen"""
    return jsonify({"success": False, "message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Loi 500 - Loi may chu"""
    logger.error("Internal server error: %s", error)
    return jsonify({"success": False, "message": "Internal server error"}), 500

# =====================================
# HAM KHOI TAO
# =====================================
def sync_id_counters():
    """Dong bo ID counters tu file JSON"""
    models = [
        ("employees", Employee),
        ("attendance", Attendance),
        ("leaves", Leave),
        ("salaries", Salary),
        ("shop_items", ShopItem),
        ("shop_transactions", ShopTransaction),
        ("notifications", Notification),
        ("projects", Project),
        ("commits", Commit),
        ("project_files", ProjectFile),
        ("contracts", Contract),
        ("otp_codes", OTP),
        ("tasks", Task)
    ]

    for file_name, model in models:
        max_id = FileHelper.get_max_id(file_name)
        model._id_counter = max_id + 1

    logger.info("Da dong bo ID counters")

# =====================================
# CREATE DEFAULT ADMIN
# =====================================
def create_default_admin():
    """Tao tai khoan admin mac dinh neu chua co"""
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
        FileHelper.append_item("employees", admin.to_dict())
        logger.info("Da tao tai khoan admin mac dinh: admin / admin123")

def check_ai_configuration():
    """Kiem tra cau hinh AI - bo qua neu chua co"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        logger.info("Da cau hinh OpenRouter API key (fallback)")
    else:
        logger.info("AI se su dung key tu giao dien cai dat (neu co)")

# =====================================
# KHOI TAO UNG DUNG
# =====================================
def init_app():
    """Khoi tao ung dung khi startup"""
    logger.info("=" * 60)
    logger.info("Khoi dong SmartEMS Application")
    logger.info("=" * 60)

    # Tao thu muc data neu chua co
    os.makedirs(Config.DATA_DIR, exist_ok=True)

    # Dong bo ID
    sync_id_counters()

    # Tao admin mac dinh
    create_default_admin()

    # Kiem tra cau hinh AI
    check_ai_configuration()

    logger.info("=" * 60)
    logger.info("Ung dung da san sang")
    logger.info("Dia chi: http://localhost:5000")
    logger.info("Moi truong: %s", os.environ.get("FLASK_ENV", "development"))
    logger.info("=" * 60)

# =====================================
# MAIN
# =====================================
if __name__ == "__main__":
    init_app()
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5000)),
        debug=Config.DEBUG
    )