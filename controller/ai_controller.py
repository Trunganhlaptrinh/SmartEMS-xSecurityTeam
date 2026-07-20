# controller/ai_controller.py
# ChatEMS - AI Assistant using OpenRouter
# Version: 6.0 - Tự nhiên nhất có thể

from flask import Blueprint, request, jsonify, session
import os
import requests
import logging
import json
from datetime import datetime
from functools import wraps
from time import time
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ============================================================
# BLUEPRINT
# ============================================================
ai_bp = Blueprint("ai", __name__)

# ============================================================
# LOGGING
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION - OPENROUTER
# ============================================================
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

# Rate Limiting
RATE_LIMIT = {}
RATE_LIMIT_MAX = 100
RATE_LIMIT_WINDOW = 60

# ============================================================
# QUAN LY NHIEU API KEY TU DATABASE (CO TEN)
# ============================================================
from util.file_helper import FileHelper

AI_CONFIG_FILE = "ai_config"

def get_ai_config():
    """Lay cau hinh AI tu file JSON"""
    configs = FileHelper.read_all(AI_CONFIG_FILE)
    if configs and len(configs) > 0:
        return configs[0]
    return {"keys": []}

def save_ai_config(config: dict):
    """Luu cau hinh AI vao file JSON"""
    FileHelper.write_all(AI_CONFIG_FILE, [config])

def get_all_api_keys():
    """Lay danh sach tat ca API keys da luu (co ten)"""
    config = get_ai_config()
    return config.get("keys", [])

def get_current_api_key():
    """Lay API key dang duoc su dung"""
    config = get_ai_config()
    return config.get("current_key")

def get_current_api_name():
    """Lay ten cua API key dang duoc su dung"""
    config = get_ai_config()
    current_key = config.get("current_key")
    if current_key:
        for key in config.get("keys", []):
            if key.get("key") == current_key:
                return key.get("name", "API khong ten")
    return None

def get_active_api_key():
    """Lay API key uu tien: tu database truoc, fallback sang .env"""
    current = get_current_api_key()
    if current:
        return current
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        logger.info("Dang su dung API Key tu file .env (fallback)")
        return env_key
    return None

def add_api_key(api_key: str, name: str = ""):
    """Them API key moi vao danh sach voi ten"""
    try:
        config = get_ai_config()
        keys = config.get("keys", [])
        
        for k in keys:
            if k.get("key") == api_key:
                return False
        
        new_key = {
            "key": api_key,
            "name": name or f"API {len(keys) + 1}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        keys.append(new_key)
        config["keys"] = keys
        
        if not config.get("current_key"):
            config["current_key"] = api_key
        
        save_ai_config(config)
        logger.info("Da them API Key moi: %s", name)
        return True
    except Exception as e:
        logger.error("Loi them API Key: %s", e)
        return False

def remove_api_key(api_key: str):
    """Xoa API key khoi danh sach"""
    try:
        config = get_ai_config()
        keys = config.get("keys", [])
        new_keys = [k for k in keys if k.get("key") != api_key]
        
        if len(new_keys) == len(keys):
            return False
        
        config["keys"] = new_keys
        
        if config.get("current_key") == api_key:
            config["current_key"] = new_keys[0].get("key") if new_keys else None
        
        save_ai_config(config)
        logger.info("Da xoa API Key khoi danh sach")
        return True
    except Exception as e:
        logger.error("Loi xoa API Key: %s", e)
        return False

def set_current_api_key(api_key: str):
    """Dat API key hien tai"""
    try:
        config = get_ai_config()
        keys = config.get("keys", [])
        for k in keys:
            if k.get("key") == api_key:
                config["current_key"] = api_key
                save_ai_config(config)
                return True
        return False
    except Exception as e:
        logger.error("Loi dat API Key: %s", e)
        return False

def get_api_status():
    """Lay trang thai cau hinh API"""
    config = get_ai_config()
    current_key = config.get("current_key")
    keys = config.get("keys", [])
    
    has_active = bool(current_key and get_active_api_key())
    has_keys = len(keys) > 0
    current_name = None
    
    if current_key:
        for k in keys:
            if k.get("key") == current_key:
                current_name = k.get("name", "API khong ten")
                break
    
    return {
        "has_active": has_active,
        "has_keys": has_keys,
        "current_name": current_name,
        "total_keys": len(keys)
    }

# ============================================================
# CHECK CONFIGURATION
# ============================================================
if not get_active_api_key():
    logger.warning("=" * 70)
    logger.warning("CHUA CAU HINH OPENROUTER API KEY!")
    logger.warning("Vui long dang nhap Admin va vao ChatEMS > Cai dat API")
    logger.warning("Hoac them vao file .env: OPENROUTER_API_KEY=your_key")
    logger.warning("=" * 70)

# ============================================================
# RATE LIMITING DECORATOR - PHAN QUYEN
# ============================================================
def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        employee_id = session.get("employee_id", "anonymous")
        role = session.get("role", "employee")
        now = time()
        
        max_requests = 200 if role == "admin" else RATE_LIMIT_MAX
        
        if employee_id not in RATE_LIMIT:
            RATE_LIMIT[employee_id] = []
        
        RATE_LIMIT[employee_id] = [t for t in RATE_LIMIT[employee_id] if now - t < RATE_LIMIT_WINDOW]
        
        if len(RATE_LIMIT[employee_id]) >= max_requests:
            logger.warning("Rate limit exceeded: %s (role: %s)", employee_id, role)
            return jsonify({
                "success": False,
                "message": f"Ban da gui qua nhieu yeu cau ({max_requests}/phut). Vui long doi {RATE_LIMIT_WINDOW} giay va thu lai.",
                "error": "RATE_LIMIT",
                "retry_after": RATE_LIMIT_WINDOW
            }), 429
        
        RATE_LIMIT[employee_id].append(now)
        return f(*args, **kwargs)
    return decorated

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def format_money(amount):
    return f"{int(amount):,}".replace(",", ".") + " d"

# ============================================================
# DATA RETRIEVAL
# ============================================================
def get_relevant_data(employee_id: int, role: str, query: str) -> dict:
    from util.file_helper import FileHelper
    
    result = {
        "has_data": False,
        "data": "",
        "type": "unknown"
    }
    
    query_lower = query.lower()
    is_admin = (role == "admin")
    
    # 1. Attendance
    if any(k in query_lower for k in ["điểm danh", "check-in", "chấm công"]):
        attendances = FileHelper.read_all("attendance")
        
        if is_admin:
            today = datetime.now().strftime("%Y-%m-%d")
            today_records = [a for a in attendances if a.get("date") == today]
            present = len([a for a in attendances if a.get("status") == "present"])
            absent = len([a for a in attendances if a.get("status") == "absent"])
            late = len([a for a in attendances if a.get("status") == "late"])
            
            result["data"] = f"""TONG QUAN DIEM DANH HE THONG

Hom nay: {len(today_records)} nguoi da diem danh
Co mat: {present} nguoi
Di muon: {late} nguoi
Vang: {absent} nguoi
Tong so ban ghi: {len(attendances)}"""
        else:
            user_attendance = [a for a in attendances if a.get("employee_id") == employee_id]
            if user_attendance:
                today = datetime.now().strftime("%Y-%m-%d")
                today_record = [a for a in user_attendance if a.get("date") == today]
                month = datetime.now().strftime("%Y-%m")
                month_records = [a for a in user_attendance if a.get("date", "").startswith(month)]
                present = len([a for a in month_records if a.get("status") == "present"])
                late = len([a for a in month_records if a.get("status") == "late"])
                absent = len([a for a in month_records if a.get("status") == "absent"])
                
                if today_record:
                    status = today_record[0].get("status", "unknown")
                    status_map = {"present": "Co mat", "absent": "Vang", "late": "Di muon"}
                    result["data"] = f"""THONG KE DIEM DANH CUA BAN

Hom nay: {status_map.get(status, status)}
Thang nay: {present} ngay co mat, {late} ngay di muon, {absent} ngay vang"""
                else:
                    result["data"] = f"""Hom nay ban chua diem danh.
Thang nay: {present} ngay co mat, {late} ngay di muon, {absent} ngay vang"""
            else:
                result["data"] = "Ban chua co du lieu diem danh nao."
        
        result["has_data"] = True
        result["type"] = "attendance"
    
    # 2. Salary
    elif any(k in query_lower for k in ["lương", "salary", "tiền lương", "thu nhập"]):
        salaries = FileHelper.read_all("salaries")
        
        if is_admin:
            total = sum(s.get("total", 0) for s in salaries)
            avg = total / len(salaries) if salaries else 0
            result["data"] = f"""TONG QUAN LUONG HE THONG

Tong quy luong: {format_money(total)}
So nhan vien: {len(salaries)}
Luong trung binh: {format_money(avg)}
Thang gan nhat: {salaries[-1].get('month', 'N/A') if salaries else 'N/A'}"""
        else:
            user_salary = [s for s in salaries if s.get("employee_id") == employee_id]
            if user_salary:
                latest = sorted(user_salary, key=lambda x: x.get("month", ""), reverse=True)[0]
                result["data"] = f"""LUONG CUA BAN

Thang: {latest.get('month', 'thang nay')}
Luong co ban: {format_money(latest.get('base', 0))}
Thuong: {format_money(latest.get('bonus', 0))}
Khau tru: {format_money(latest.get('deduction', 0))}
Thuc nhan: {format_money(latest.get('total', 0))}"""
            else:
                result["data"] = "Chua co du lieu luong cho ban."
        
        result["has_data"] = True
        result["type"] = "salary"
    
    # 3. Leave
    elif any(k in query_lower for k in ["nghỉ", "phép", "leave", "ngày nghỉ"]):
        leaves = FileHelper.read_all("leaves")
        
        if is_admin:
            pending = [l for l in leaves if l.get("status") == "pending"]
            approved = [l for l in leaves if l.get("status") == "approved"]
            rejected = [l for l in leaves if l.get("status") == "rejected"]
            result["data"] = f"""TONG QUAN NGHI PHEP HE THONG

Cho duyet: {len(pending)} don
Da duyet: {len(approved)} don
Tu choi: {len(rejected)} don
Tong so don: {len(leaves)}"""
        else:
            user_leaves = [l for l in leaves if l.get("employee_id") == employee_id]
            if user_leaves:
                pending = [l for l in user_leaves if l.get("status") == "pending"]
                approved = [l for l in user_leaves if l.get("status") == "approved"]
                rejected = [l for l in user_leaves if l.get("status") == "rejected"]
                result["data"] = f"""NGHI PHEP CUA BAN

Cho duyet: {len(pending)} don
Da duyet: {len(approved)} don
Tu choi: {len(rejected)} don
Tong so don: {len(user_leaves)}"""
            else:
                result["data"] = "Ban chua co don nghi phep nao."
        
        result["has_data"] = True
        result["type"] = "leave"
    
    # 4. Notification
    elif any(k in query_lower for k in ["thông báo", "notification", "tin nhắn"]):
        notifications = FileHelper.read_all("notifications")
        
        if is_admin:
            total = len(notifications)
            active = len([n for n in notifications if n.get("status") == "active"])
            result["data"] = f"""THONG KE THONG BAO

Tong so: {total} thong bao
Dang hien thi: {active}
Da luu tru: {total - active}"""
        else:
            user_noti = [n for n in notifications if n.get("employee_id") == employee_id or n.get("is_global", False)]
            unread = [n for n in user_noti if not n.get("is_read", False)]
            result["data"] = f"""THONG BAO CUA BAN

Chua doc: {len(unread)} thong bao
Da doc: {len(user_noti) - len(unread)}
Tong so: {len(user_noti)}"""
        
        result["has_data"] = True
        result["type"] = "notification"
    
    # 5. Project
    elif any(k in query_lower for k in ["dự án", "project", "công việc"]):
        projects = FileHelper.read_all("projects")
        
        if is_admin:
            active = len([p for p in projects if p.get("status") == "active"])
            completed = len([p for p in projects if p.get("status") == "completed"])
            result["data"] = f"""TONG QUAN DU AN

Tong so: {len(projects)} du an
Dang thuc hien: {active}
Da hoan thanh: {completed}"""
        else:
            user_projects = [p for p in projects if p.get("employee_id") == employee_id]
            result["data"] = f"Ban dang tham gia {len(user_projects)} du an."
        
        result["has_data"] = True
        result["type"] = "project"
    
    # 6. Employee (Admin only)
    elif is_admin and any(k in query_lower for k in ["nhân viên", "employee", "người dùng"]):
        employees = FileHelper.read_all("employees")
        total = len(employees)
        admin_count = len([e for e in employees if e.get("role") == "admin"])
        user_count = len([e for e in employees if e.get("role") == "employee"])
        
        result["data"] = f"""TONG QUAN NHAN SU

Tong so: {total} nhan vien
Quan tri vien: {admin_count} nguoi
Nhan vien: {user_count} nguoi
Phong ban: {len(set(e.get('department', '') for e in employees if e.get('department')))}"""
        result["has_data"] = True
        result["type"] = "employee"
    
    return result

# fix prompt ở đoạn này cho tự nhiên lại mất mịa 2h vì cái này

# ============================================================
# CALL OPENROUTER API - TỰ NHIÊN NHẤT
# ============================================================
def call_openrouter(prompt: str, context: list = None, real_data: str = None, role: str = "employee") -> dict:
    """
    Goi OpenRouter API voi context va du lieu thuc te
    """
    api_key = get_active_api_key()
    
    if not api_key:
        return {
            "success": False,
            "reply": "AI chua duoc cau hinh. Vui long yeu cau Admin cau hinh API Key.",
            "error": "API_KEY_MISSING"
        }
    
    try:
        # ===== SYSTEM PROMPT TỐI GIẢN - TỰ NHIÊN NHẤT =====
        system_prompt = """Ban la ChatEMS, tro ly AI cua he thong SmartEMS.

Hay tro chuyen tu nhien nhu mot nguoi ban.
Tra loi bang tieng Viet co dau, than thien, vui ve.

Khi co du lieu thuc te, hay dung no.
Khi khong co, hay tra loi bang kien thuc chung cua ban.
Dung tu choi cau hoi cua nguoi dung."""
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add real data
        if real_data:
            messages.append({
                "role": "user",
                "content": f"DU LIEU THUC TE:\n{real_data}"
            })
        
        # Add conversation context
        if context:
            for ctx in context[-5:]:
                if ctx.get("user"):
                    messages.append({"role": "user", "content": ctx["user"]})
                if ctx.get("assistant"):
                    messages.append({"role": "assistant", "content": ctx["assistant"]})
        
        # Add current question
        messages.append({"role": "user", "content": prompt})
        
        # Log request
        logger.info("OpenRouter request - Role: %s", role)
        logger.info("Prompt: %s...", prompt[:100])
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "SmartEMS Chat"
        }
        
        # Prepare payload
        payload = {
            "model": "openrouter/free",
            "messages": messages,
            "temperature": 0.9,
            "max_tokens": 1024,
            "top_p": 0.95
        }
        
        # Make API call
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        logger.info("OpenRouter response status: %s", response.status_code)
        
        # Parse response
        if response.status_code == 200:
            try:
                data = response.json()
                
                reply = None
                
                # 1. Format OpenAI
                if "choices" in data and len(data["choices"]) > 0:
                    if "message" in data["choices"][0]:
                        reply = data["choices"][0]["message"]["content"]
                    elif "text" in data["choices"][0]:
                        reply = data["choices"][0]["text"]
                
                # 2. Format Gemini
                if not reply and "candidates" in data and len(data["candidates"]) > 0:
                    if "content" in data["candidates"][0]:
                        parts = data["candidates"][0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            reply = parts[0]["text"]
                
                # 3. Fallback
                if not reply and "data" in data:
                    if "text" in data["data"]:
                        reply = data["data"]["text"]
                    elif "response" in data["data"]:
                        reply = data["data"]["response"]
                
                if reply:
                    return {"success": True, "reply": reply.strip()}
                
                logger.error("Khong the parse OpenRouter response")
                return {
                    "success": False,
                    "reply": "Xin loi, khong the lay du lieu tu AI. Vui long thu lai.",
                    "error": "PARSE_ERROR"
                }
                
            except Exception as e:
                logger.error("Parse OpenRouter response error: %s", e)
                return {
                    "success": False,
                    "reply": f"Xin loi, co loi xu ly du lieu tu AI: {str(e)}",
                    "error": "PARSE_ERROR"
                }
        else:
            error_msg = "Loi ket noi AI"
            try:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            except:
                error_msg = f"HTTP {response.status_code}"
            
            logger.error("OpenRouter error: %s - %s", response.status_code, error_msg)
            
            if response.status_code == 401:
                return {
                    "success": False,
                    "reply": "API Key khong hop le. Vui long kiem tra lai.",
                    "error": "UNAUTHORIZED"
                }
            elif response.status_code == 429:
                return {
                    "success": False,
                    "reply": "Qua nhieu yeu cau. Vui long doi mot chut va thu lai.",
                    "error": "RATE_LIMIT"
                }
            else:
                return {
                    "success": False,
                    "reply": f"Xin loi, co loi ket noi AI: {error_msg}",
                    "error": f"HTTP_{response.status_code}"
                }
            
    except requests.exceptions.Timeout:
        logger.error("OpenRouter timeout")
        return {
            "success": False,
            "reply": "AI phan hoi qua cham. Vui long thu lai sau.",
            "error": "TIMEOUT"
        }
    except requests.exceptions.ConnectionError:
        logger.error("OpenRouter connection error")
        return {
            "success": False,
            "reply": "Khong the ket noi den AI. Vui long kiem tra mang.",
            "error": "CONNECTION_ERROR"
        }
    except Exception as e:
        logger.error("OpenRouter error: %s", e)
        return {
            "success": False,
            "reply": f"Xin loi, co loi xay ra: {str(e)}",
            "error": "UNKNOWN"
        }

# ============================================================
# ROUTES - CHAT
# ============================================================

@ai_bp.route("/chat", methods=["POST"])
@rate_limit
def chat():
    """Process chat messages with AI"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Vui long dang nhap"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Du lieu khong hop le"}), 400
            
        message = data.get("message", "").strip()
        context = data.get("context", [])
        
        if not message:
            return jsonify({"success": False, "message": "Vui long nhap tin nhan"}), 400
        
        employee_id = session["employee_id"]
        employee_name = session.get("name", "Nhan vien")
        role = session.get("role", "employee")
        
        logger.info("Chat - [%s] %s: %s...", role, employee_name, message[:100])
        
        # Get relevant data
        real_data_result = get_relevant_data(employee_id, role, message)
        real_data = real_data_result["data"] if real_data_result["has_data"] else None
        
        # Build prompt
        user_context = f"User: {employee_name} (ID: {employee_id}, Role: {role})"
        enhanced_prompt = f"{user_context}\nCau hoi: {message}"
        
        # Call OpenRouter
        result = call_openrouter(enhanced_prompt, context, real_data, role)
        
        return jsonify({
            "success": result["success"],
            "reply": result["reply"],
            "has_real_data": real_data_result["has_data"],
            "data_type": real_data_result["type"],
            "role": role,
            "error": result.get("error")
        })
        
    except Exception as e:
        logger.error("Chat error: %s", e)
        return jsonify({"success": False, "message": f"Loi server: {str(e)}"}), 500


@ai_bp.route("/health", methods=["GET"])
def health_check():
    """Check AI connection status"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chua dang nhap"}), 401
    
    api_key = get_active_api_key()
    is_configured = bool(api_key)
    api_status = get_api_status()
    
    result = {
        "success": True,
        "provider": "OpenRouter",
        "model": MODEL,
        "configured": is_configured,
        "role": session.get("role", "employee"),
        "rate_limit": {"max": RATE_LIMIT_MAX, "window": RATE_LIMIT_WINDOW},
        "api_status": api_status
    }
    
    if is_configured:
        try:
            test_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000"
            }
            test_payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            test_response = requests.post(
                OPENROUTER_URL,
                headers=test_headers,
                json=test_payload,
                timeout=5
            )
            result["api_valid"] = test_response.status_code == 200
            result["api_status_code"] = test_response.status_code
            if test_response.status_code != 200:
                result["api_error"] = test_response.text[:200]
        except Exception as e:
            result["api_valid"] = False
            result["api_error"] = str(e)
    else:
        result["api_valid"] = False
    
    if is_configured and result.get("api_valid"):
        result["message"] = "AI da san sang"
        result["status"] = "ready"
    elif is_configured:
        result["message"] = "API key khong hop le"
        result["status"] = "error"
    else:
        result["message"] = "AI chua duoc cau hinh"
        result["status"] = "unconfigured"
    
    return jsonify(result)


@ai_bp.route("/models", methods=["GET"])
def get_models():
    """Get list of available models (Admin only)"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chua dang nhap"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Khong co quyen"}), 403
    
    return jsonify({
        "success": True,
        "data": {
            "current": MODEL,
            "free_models": [
                "openrouter/free",
                "google/gemini-2.0-flash-exp:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "microsoft/phi-3-mini-128k-instruct:free",
                "mistralai/mistral-7b-instruct:free",
                "qwen/qwen-2.5-7b-instruct:free"
            ]
        }
    })


@ai_bp.route("/clear-context", methods=["POST"])
def clear_context():
    """Clear conversation context"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chua dang nhap"}), 401
    
    return jsonify({"success": True, "message": "Da xoa ngu canh hoi thoai"})

# ============================================================
# ADMIN API - QUAN LY NHIEU API KEY (CO TEN)
# ============================================================

@ai_bp.route("/admin/config", methods=["GET"])
def get_admin_config():
    """Admin xem danh sach API keys (an key)"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Vui long dang nhap"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Khong co quyen"}), 403
    
    config = get_ai_config()
    keys = config.get("keys", [])
    current = config.get("current_key")
    
    masked_keys = []
    for k in keys:
        key = k.get("key", "")
        if len(key) > 8:
            masked = key[:4] + "..." + key[-4:]
        else:
            masked = "***"
        masked_keys.append({
            "key": key,
            "masked": masked,
            "name": k.get("name", "API khong ten"),
            "created_at": k.get("created_at", "")
        })
    
    current_name = None
    if current:
        for k in keys:
            if k.get("key") == current:
                current_name = k.get("name", "API khong ten")
                break
    
    return jsonify({
        "success": True,
        "keys": masked_keys,
        "current_key": current,
        "current_name": current_name,
        "count": len(keys),
        "has_active": bool(current)
    })


@ai_bp.route("/admin/config", methods=["POST"])
def add_admin_config():
    """Admin them API Key moi (co ten)"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Vui long dang nhap"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Khong co quyen"}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Du lieu khong hop le"}), 400
            
        api_key = data.get("api_key", "").strip()
        name = data.get("name", "").strip()
        
        if not api_key:
            return jsonify({"success": False, "message": "API Key khong duoc de trong"}), 400
        
        if not api_key.startswith("sk-or-v1-"):
            return jsonify({
                "success": False, 
                "message": "API Key khong hop le. Key phai bat dau bang 'sk-or-v1-'"
            }), 400
        
        # Kiem tra key co hop le khong
        try:
            test_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000"
            }
            test_payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            test_response = requests.post(
                OPENROUTER_URL,
                headers=test_headers,
                json=test_payload,
                timeout=10
            )
            
            if test_response.status_code != 200:
                error_msg = test_response.json().get("error", {}).get("message", "Khong xac dinh")
                return jsonify({
                    "success": False,
                    "message": f"API Key khong hop le. Loi: {error_msg}"
                }), 400
                
        except requests.exceptions.ConnectionError:
            return jsonify({
                "success": False,
                "message": "Khong the ket noi den OpenRouter. Vui long kiem tra mang."
            }), 500
        except requests.exceptions.Timeout:
            return jsonify({
                "success": False,
                "message": "Ket noi den OpenRouter bi timeout. Vui long thu lai."
            }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Loi ket noi OpenRouter: {str(e)}"
            }), 500
        
        if not name:
            name = f"API {datetime.now().strftime('%H:%M')}"
            
        if add_api_key(api_key, name):
            logger.info("Admin %s da them API Key: %s", session.get("name"), name)
            return jsonify({
                "success": True,
                "message": f"Da them API Key '{name}' thanh cong."
            })
        else:
            return jsonify({
                "success": False,
                "message": "API Key nay da ton tai."
            }), 400
            
    except Exception as e:
        logger.error("Loi add_admin_config: %s", e)
        return jsonify({
            "success": False,
            "message": f"Loi server: {str(e)}"
        }), 500


@ai_bp.route("/admin/config/use", methods=["POST"])
def use_admin_config():
    """Admin chon API Key de su dung"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Vui long dang nhap"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Khong co quyen"}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Du lieu khong hop le"}), 400
            
        api_key = data.get("api_key", "").strip()
        
        if not api_key:
            return jsonify({"success": False, "message": "API Key khong duoc de trong"}), 400
        
        if set_current_api_key(api_key):
            config = get_ai_config()
            name = None
            for k in config.get("keys", []):
                if k.get("key") == api_key:
                    name = k.get("name", "API khong ten")
                    break
            
            logger.info("Admin %s da chuyen sang API Key: %s", session.get("name"), name)
            return jsonify({
                "success": True,
                "message": f"Da chuyen sang API Key '{name}'"
            })
        else:
            return jsonify({
                "success": False,
                "message": "API Key khong ton tai"
            }), 404
            
    except Exception as e:
        logger.error("Loi use_admin_config: %s", e)
        return jsonify({
            "success": False,
            "message": f"Loi server: {str(e)}"
        }), 500


@ai_bp.route("/admin/config", methods=["DELETE"])
def delete_admin_config():
    """Admin xoa API Key"""
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Vui long dang nhap"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Khong co quyen"}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Du lieu khong hop le"}), 400
            
        api_key = data.get("api_key", "").strip()
        
        if not api_key:
            return jsonify({"success": False, "message": "API Key khong duoc de trong"}), 400
        
        config = get_ai_config()
        name = None
        for k in config.get("keys", []):
            if k.get("key") == api_key:
                name = k.get("name", "API khong ten")
                break
        
        if remove_api_key(api_key):
            logger.info("Admin %s da xoa API Key: %s", session.get("name"), name)
            return jsonify({
                "success": True,
                "message": f"Da xoa API Key '{name}'"
            })
        else:
            return jsonify({
                "success": False,
                "message": "API Key khong ton tai"
            }), 404
            
    except Exception as e:
        logger.error("Loi delete_admin_config: %s", e)
        return jsonify({
            "success": False,
            "message": f"Loi server: {str(e)}"
        }), 500