# util/file_helper.py
# util: đọc và ghi dữ liệu vào file JSON (thay thế database)
# tương tự như việc Java dùng ArrayList + lưu xuống file

import json
import os

# đường dẫn tới thư mục data (tự tạo nếu chưa có)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class FileHelper:

    # đảm bảo thư mục data tồn tại
    @staticmethod
    def _ensure_dir():
        os.makedirs(DATA_DIR, exist_ok=True)

    # lấy đường dẫn đầy đủ của file JSON theo tên
    # ví dụ: _get_path("employees") → "data/employees.json"
    @staticmethod
    def _get_path(file_name: str) -> str:
        return os.path.join(DATA_DIR, f"{file_name}.json")

    # đọc toàn bộ dữ liệu từ file JSON → trả về list dict
    # tương tự: đọc ArrayList từ file trong Java
    @staticmethod
    def read_all(file_name: str) -> list:
        FileHelper._ensure_dir()
        path = FileHelper._get_path(file_name)

        # nếu file chưa tồn tại → trả về list rỗng
        if not os.path.exists(path):
            return []

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ghi toàn bộ list dict vào file JSON (ghi đè)
    # tương tự: lưu ArrayList xuống file trong Java
    @staticmethod
    def write_all(file_name: str, data: list):
        FileHelper._ensure_dir()
        path = FileHelper._get_path(file_name)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            # ensure_ascii=False để lưu được tiếng Việt
            # indent=2 để file dễ đọc

    # thêm 1 item vào file (đọc ra → append → ghi lại)
    @staticmethod
    def append_item(file_name: str, item: dict):
        data = FileHelper.read_all(file_name)
        data.append(item)
        FileHelper.write_all(file_name, data)

    # cập nhật 1 item theo id (tìm → sửa → ghi lại)
    @staticmethod
    def update_item(file_name: str, item_id: int, updated: dict) -> bool:
        data = FileHelper.read_all(file_name)
        for i, item in enumerate(data):
            if item["id"] == item_id:
                data[i] = updated
                FileHelper.write_all(file_name, data)
                return True
        return False  # không tìm thấy id

    # xóa 1 item theo id
    @staticmethod
    def delete_item(file_name: str, item_id: int) -> bool:
        data = FileHelper.read_all(file_name)
        new_data = [item for item in data if item["id"] != item_id]
        if len(new_data) == len(data):
            return False  # không tìm thấy, không xóa được
        FileHelper.write_all(file_name, new_data)
        return True

    # lấy id lớn nhất hiện có trong file để tự tăng ID đúng khi khởi động
    @staticmethod
    def get_max_id(file_name: str) -> int:
        data = FileHelper.read_all(file_name)
        if not data:
            return 0
        return max(item["id"] for item in data)
