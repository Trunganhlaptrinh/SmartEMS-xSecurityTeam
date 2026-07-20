# util/crypto_helper.py
# Helper: Mã hóa và giải mã dữ liệu nhạy cảm

from cryptography.fernet import Fernet
import base64
import hashlib
import os

class CryptoHelper:
    
    # Khóa mã hóa (nên đặt trong biến môi trường)
    # Nếu không có, sẽ tạo khóa cố định (vẫn an toàn hơn lưu plaintext)
    _KEY = None
    
    @staticmethod
    def get_key():
        """Lấy khóa mã hóa từ biến môi trường hoặc tạo khóa cố định"""
        if CryptoHelper._KEY is not None:
            return CryptoHelper._KEY
        
        # Ưu tiên lấy từ biến môi trường
        key = os.environ.get("CRYPTO_KEY", "")
        if key:
            CryptoHelper._KEY = key.encode()
            return CryptoHelper._KEY
        
        # Nếu không có, tạo khóa cố định từ secret (vẫn an toàn hơn plaintext)
        # Khóa này sẽ luôn giống nhau giữa các lần chạy
        secret = "SmartEMS_Secret_Key_2024_For_Email_Bot_Password_Encryption"
        key_bytes = hashlib.sha256(secret.encode()).digest()
        CryptoHelper._KEY = base64.urlsafe_b64encode(key_bytes)
        return CryptoHelper._KEY
    
    @staticmethod
    def encrypt(text: str) -> str:
        """Mã hóa văn bản"""
        if not text:
            return ""
        try:
            key = CryptoHelper.get_key()
            f = Fernet(key)
            encrypted = f.encrypt(text.encode())
            return encrypted.decode()
        except Exception as e:
            print(f"Lỗi mã hóa: {e}")
            return text
    
    @staticmethod
    def decrypt(encrypted_text: str) -> str:
        """Giải mã văn bản"""
        if not encrypted_text:
            return ""
        try:
            key = CryptoHelper.get_key()
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception as e:
            print(f"Lỗi giải mã: {e}")
            return encrypted_text
    
    @staticmethod
    def is_encrypted(text: str) -> bool:
        """Kiểm tra xem text có phải là dữ liệu đã mã hóa không"""
        if not text:
            return False
        try:
            decrypted = CryptoHelper.decrypt(text)
            return decrypted != text
        except:
            return False