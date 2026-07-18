# util/email_helper.py
# Helper: Gửi email OTP qua Brevo HTTP API (thay vì SMTP để tránh bị Render Free chặn cổng 465/587)

import json
import random
import requests
from pathlib import Path
from util.crypto_helper import CryptoHelper

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailHelper:

    @staticmethod
    def get_config_file_path():
        """Đường dẫn đến file cấu hình email"""
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "email_config.json"

    @staticmethod
    def load_config():
        """Đọc cấu hình email từ file JSON"""
        config_path = EmailHelper.get_config_file_path()

        if not config_path.exists():
            default_config = {"bots": []}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"bots": []}

    @staticmethod
    def save_config(config: dict) -> bool:
        """Lưu cấu hình email vào file JSON"""
        try:
            config_path = EmailHelper.get_config_file_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi lưu cấu hình email: {e}")
            return False

    @staticmethod
    def get_bots():
        """Lấy danh sách các bot đã cấu hình"""
        config = EmailHelper.load_config()
        return config.get("bots", [])

    @staticmethod
    def get_active_bots():
        """Lấy danh sách bot đang hoạt động (có is_active = True)"""
        bots = EmailHelper.get_bots()
        return [b for b in bots if b.get("is_active", True)]

    @staticmethod
    def get_random_bot():
        """Chọn ngẫu nhiên 1 bot đang hoạt động để gửi email"""
        active_bots = EmailHelper.get_active_bots()
        if not active_bots:
            return None
        return random.choice(active_bots)

    @staticmethod
    def add_bot(sender: str, password: str, name: str = "") -> bool:
        """
        Thêm một bot mới.
        LƯU Ý: 'password' giờ là API KEY của Brevo (không phải mật khẩu Gmail),
        'sender' phải là email đã được xác minh (verified sender) trên Brevo.
        """
        config = EmailHelper.load_config()
        bots = config.get("bots", [])

        for bot in bots:
            if bot["sender"] == sender:
                return False

        encrypted_password = CryptoHelper.encrypt(password)

        bots.append({
            "sender": sender,
            "password_hash": encrypted_password,  # thực chất lưu API key đã mã hoá
            "name": name or sender,
            "is_active": True,
            "created_at": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        config["bots"] = bots
        return EmailHelper.save_config(config)

    @staticmethod
    def update_bot(sender: str, password: str = None, name: str = None, is_active: bool = None) -> bool:
        """Cập nhật thông tin bot"""
        config = EmailHelper.load_config()
        bots = config.get("bots", [])

        for i, bot in enumerate(bots):
            if bot["sender"] == sender:
                if password is not None:
                    bots[i]["password_hash"] = CryptoHelper.encrypt(password)
                if name is not None:
                    bots[i]["name"] = name
                if is_active is not None:
                    bots[i]["is_active"] = is_active
                config["bots"] = bots
                return EmailHelper.save_config(config)

        return False

    @staticmethod
    def delete_bot(sender: str) -> bool:
        """Xóa bot theo email"""
        config = EmailHelper.load_config()
        bots = config.get("bots", [])

        new_bots = [b for b in bots if b["sender"] != sender]
        if len(new_bots) == len(bots):
            return False

        config["bots"] = new_bots
        return EmailHelper.save_config(config)

    @staticmethod
    def has_active_bot() -> bool:
        """Kiểm tra có ít nhất 1 bot đang hoạt động không"""
        return len(EmailHelper.get_active_bots()) > 0

    @staticmethod
    def is_configured() -> bool:
        """Kiểm tra xem đã cấu hình email chưa"""
        return EmailHelper.has_active_bot()

    @staticmethod
    def _build_html(username: str, otp_code: str) -> str:
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{
                    max-width: 500px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #e4e7ec;
                    border-radius: 10px;
                    background: #f8f9fc;
                }}
                .code {{
                    font-size: 36px;
                    font-weight: 700;
                    color: #4255ff;
                    text-align: center;
                    padding: 20px;
                    background: #eef0ff;
                    border-radius: 8px;
                    letter-spacing: 10px;
                    font-family: 'Courier New', monospace;
                }}
                .info {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-top: 16px;
                    padding: 12px;
                    background: #f0f4ff;
                    border-radius: 6px;
                }}
                .warning {{
                    color: #e53935;
                    font-size: 13px;
                    margin-top: 12px;
                }}
                .footer {{
                    color: #9ca3af;
                    font-size: 12px;
                    text-align: center;
                    margin-top: 16px;
                    border-top: 1px solid #e4e7ec;
                    padding-top: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color:#1a1d23;">Xác thực đăng nhập SmartEMS</h2>
                <p>Xin chào <strong>{username}</strong>,</p>
                <p>Mã xác thực (OTP) của bạn là:</p>
                <div class="code">{otp_code}</div>
                <div class="info">
                    ⏰ Mã có hiệu lực trong <strong>5 phút</strong><br>
                    📧 Email này được gửi tự động từ hệ thống SmartEMS
                </div>
                <p class="warning">
                    ⚠️ Nếu bạn không yêu cầu đăng nhập, vui lòng bỏ qua email này.
                </p>
                <div class="footer">
                    SmartEMS - Hệ thống quản lý nhân sự
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def _send_via_brevo(api_key: str, sender_email: str, sender_name: str,
                         to_email: str, subject: str, html_content: str) -> bool:
        """Gửi email qua Brevo HTTP API. Timeout ngắn để không treo worker."""
        payload = {
            "sender": {"name": sender_name or sender_email, "email": sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        try:
            resp = requests.post(BREVO_API_URL, headers=headers, json=payload, timeout=8)
            if resp.status_code in (200, 201):
                return True
            print(f"❌ Brevo trả về lỗi {resp.status_code}: {resp.text}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi kết nối Brevo: {e}")
            return False

    @staticmethod
    def send_otp_email(recipient_email: str, otp_code: str, username: str) -> bool:
        """
        Gửi mã OTP qua email - Chọn ngẫu nhiên 1 bot (sender+API key) đang hoạt động
        Trả về True nếu gửi thành công, False nếu thất bại
        """
        bot = EmailHelper.get_random_bot()

        if not bot:
            print("=" * 70)
            print("KHÔNG CÓ EMAIL BOT NÀO ĐANG HOẠT ĐỘNG!")
            print("Vui lòng thêm email bot (sender + API key Brevo) trong trang Quản lý nhân viên")
            print(f"Mã OTP cho {username} ({recipient_email}): {otp_code}")
            print("=" * 70)
            return False

        subject = "Mã xác thực SmartEMS"
        content = EmailHelper._build_html(username, otp_code)

        encrypted_key = bot.get("password_hash", "")
        if not encrypted_key:
            print(f"Không tìm thấy API key cho bot {bot['sender']}")
            return False

        api_key = CryptoHelper.decrypt(encrypted_key)
        if not api_key:
            print(f"Không thể giải mã API key cho bot {bot['sender']}")
            return False

        ok = EmailHelper._send_via_brevo(
            api_key, bot["sender"], bot.get("name", bot["sender"]),
            recipient_email, subject, content
        )
        if ok:
            print(f"✅ Đã gửi OTP từ {bot['sender']} đến {recipient_email} ({username})")
            return True

        print(f"📧 [DEBUG] Mã OTP cho {username}: {otp_code}")

        # Fallback: thử bot khác nếu có
        active_bots = EmailHelper.get_active_bots()
        for try_bot in active_bots:
            if try_bot["sender"] == bot["sender"]:
                continue
            encrypted_key = try_bot.get("password_hash", "")
            if not encrypted_key:
                continue
            api_key = CryptoHelper.decrypt(encrypted_key)
            if not api_key:
                continue
            ok = EmailHelper._send_via_brevo(
                api_key, try_bot["sender"], try_bot.get("name", try_bot["sender"]),
                recipient_email, subject, content
            )
            if ok:
                print(f"✅ Đã gửi OTP từ {try_bot['sender']} (fallback) đến {recipient_email}")
                return True

        return False

    @staticmethod
    def get_user_email(employee_id: int) -> str:
        """Lấy email của user từ database"""
        from util.file_helper import FileHelper

        employees = FileHelper.read_all("employees")
        emp = next((e for e in employees if e["id"] == employee_id), None)

        if not emp:
            return None

        if "@" in emp["username"]:
            return emp["username"]

        return emp.get("email") or f"{emp['username']}@smartems.com"