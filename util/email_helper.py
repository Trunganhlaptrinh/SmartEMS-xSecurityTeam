# util/email_helper.py
# Helper: Gửi email OTP - Hỗ trợ nhiều bot với mã hóa mật khẩu

import yagmail
import json
import random
from pathlib import Path
from util.crypto_helper import CryptoHelper

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
        except:
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
        """Thêm một bot mới - Mã hóa mật khẩu trước khi lưu"""
        config = EmailHelper.load_config()
        bots = config.get("bots", [])
        
        # Kiểm tra trùng email
        for bot in bots:
            if bot["sender"] == sender:
                return False
        
        # Mã hóa mật khẩu trước khi lưu
        encrypted_password = CryptoHelper.encrypt(password)
        
        bots.append({
            "sender": sender,
            "password_hash": encrypted_password,  # Đổi tên thành password_hash để đánh lừa
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
                    # Mã hóa mật khẩu mới
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
    def send_otp_email(recipient_email: str, otp_code: str, username: str) -> bool:
        """
        Gửi mã OTP qua email - Chọn ngẫu nhiên 1 bot đang hoạt động
        Trả về True nếu gửi thành công, False nếu thất bại
        """
        # Lấy bot ngẫu nhiên
        bot = EmailHelper.get_random_bot()
        
        if not bot:
            print("=" * 70)
            print("KHÔNG CÓ EMAIL BOT NÀO ĐANG HOẠT ĐỘNG!")
            print("Vui lòng thêm email bot trong trang Quản lý nhân viên")
            print(f"Mã OTP cho {username} ({recipient_email}): {otp_code}")
            print("=" * 70)
            return False
        
        try:
            # Lấy password đã mã hóa (tên trường là password_hash)
            encrypted_password = bot.get("password_hash", "")
            if not encrypted_password:
                print(f"Không tìm thấy mật khẩu cho bot {bot['sender']}")
                return False
            
            # Giải mã mật khẩu
            password = CryptoHelper.decrypt(encrypted_password)
            if not password:
                print(f"Không thể giải mã mật khẩu cho bot {bot['sender']}")
                return False
            
            # Khởi tạo yagmail với email bot
            yag = yagmail.SMTP(bot["sender"], password)
            
            # Nội dung email
            subject = "Mã xác thực SmartEMS"
            content = f"""
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
            
            # Gửi email
            yag.send(
                to=recipient_email,
                subject=subject,
                contents=content
            )
            
            print(f"✅ Đã gửi OTP từ {bot['sender']} đến {recipient_email} ({username})")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi gửi email từ {bot['sender']} đến {recipient_email}: {e}")
            print(f"📧 [DEBUG] Mã OTP cho {username}: {otp_code}")
            
            # Nếu bot này lỗi, thử bot khác (fallback)
            active_bots = EmailHelper.get_active_bots()
            if len(active_bots) > 1:
                for try_bot in active_bots:
                    if try_bot["sender"] == bot["sender"]:
                        continue
                    try:
                        encrypted_password = try_bot.get("password_hash", "")
                        if not encrypted_password:
                            continue
                        password = CryptoHelper.decrypt(encrypted_password)
                        if not password:
                            continue
                        yag = yagmail.SMTP(try_bot["sender"], password)
                        yag.send(
                            to=recipient_email,
                            subject=subject,
                            contents=content
                        )
                        print(f"✅ Đã gửi OTP từ {try_bot['sender']} (fallback) đến {recipient_email}")
                        return True
                    except:
                        continue
            
            return False

    @staticmethod
    def get_user_email(employee_id: int) -> str:
        """
        Lấy email của user từ database
        """
        from util.file_helper import FileHelper
        
        employees = FileHelper.read_all("employees")
        emp = next((e for e in employees if e["id"] == employee_id), None)
        
        if not emp:
            return None
        
        if "@" in emp["username"]:
            return emp["username"]
        
        return emp.get("email") or f"{emp['username']}@smartems.com"