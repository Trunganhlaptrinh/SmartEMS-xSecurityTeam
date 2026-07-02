# util/auth_helper.py
# util: hash mật khẩu và kiểm tra session đăng nhập

import hashlib
import os

class AuthHelper:

    # hash mật khẩu bằng SHA-256 (đơn giản, phù hợp bài học)
    # tương tự: không có trong Java Console App vì không cần login
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # kiểm tra mật khẩu khớp với hash đã lưu
    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        return AuthHelper.hash_password(password) == hashed

    # tạo token session đơn giản (random hex)
    @staticmethod
    def generate_token() -> str:
        return os.urandom(24).hex()
