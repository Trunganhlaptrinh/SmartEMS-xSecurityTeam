# util/file_helper.py
# util: đọc và ghi dữ liệu vào file JSON (thay thế database)
# tương tự như việc Java dùng ArrayList + lưu xuống file
#
# ĐÃ NÂNG CẤP (bản chuyên nghiệp cho web nội bộ nhiều người dùng cùng lúc):
#   1. Khóa (lock) riêng cho từng file -> tránh 2 người cùng lưu 1 lúc làm
#      hỏng dữ liệu (race condition), đây chính là nguyên nhân khiến
#      project_files.json từng bị lỗi JSON và làm sập cả server lúc khởi động.
#   2. Ghi file kiểu "atomic" (ghi ra file tạm rồi mới đổi tên) -> nếu server
#      tắt đột ngột giữa lúc đang ghi, file gốc vẫn nguyên vẹn, không bị half-write.
#   3. Nếu 1 file JSON lỡ bị hỏng, không cho sập cả server nữa: tự động sao lưu
#      file lỗi sang <file>.corrupt-<timestamp>.json và trả về danh sách rỗng,
#      đồng thời in cảnh báo rõ ràng ra console để biết mà kiểm tra lại.

import json
import os
import threading
import shutil
from datetime import datetime

# đường dẫn tới thư mục data (tự tạo nếu chưa có)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class FileHelper:

    # mỗi tên file dữ liệu (vd "employees", "contracts") có 1 Lock riêng,
    # để nhiều request từ nhiều người dùng khác nhau ghi cùng lúc không đè lên nhau
    _locks = {}
    _locks_guard = threading.Lock()

    @staticmethod
    def _get_lock(file_name: str) -> threading.Lock:
        with FileHelper._locks_guard:
            if file_name not in FileHelper._locks:
                FileHelper._locks[file_name] = threading.Lock()
            return FileHelper._locks[file_name]

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

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
            # KHÔNG để 1 file hỏng làm sập cả server.
            # Sao lưu file lỗi lại để còn kiểm tra/khôi phục thủ công sau,
            # sau đó coi như file này rỗng để các tính năng khác vẫn chạy được.
            backup_name = f"{file_name}.corrupt-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(DATA_DIR, backup_name)
            try:
                shutil.copy2(path, backup_path)
            except Exception:
                pass
            print(
                f"[FileHelper] ❌ File dữ liệu '{file_name}.json' bị lỗi JSON ({e}). "
                f"Đã sao lưu bản lỗi sang '{backup_name}' và dùng danh sách rỗng để server "
                f"không bị sập. Vui lòng kiểm tra lại file backup này!"
            )
            return []

    # ghi toàn bộ list dict vào file JSON (ghi đè) — kiểu ATOMIC:
    # ghi ra file tạm trước, chỉ khi ghi xong hoàn toàn mới đổi tên đè lên file thật.
    # Nhờ vậy nếu server tắt/lỗi giữa chừng, file dữ liệu gốc vẫn không bị hỏng.
    @staticmethod
    def write_all(file_name: str, data: list):
        FileHelper._ensure_dir()
        path = FileHelper._get_path(file_name)
        tmp_path = path + ".tmp"

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            # ensure_ascii=False để lưu được tiếng Việt
            # indent=2 để file dễ đọc
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)  # đổi tên atomic, không có trạng thái "ghi dở"

    # thêm 1 item vào file (đọc ra → append → ghi lại)
    # bọc trong lock để 2 người thêm cùng lúc không bị mất dữ liệu của nhau
    @staticmethod
    def append_item(file_name: str, item: dict):
        lock = FileHelper._get_lock(file_name)
        with lock:
            data = FileHelper.read_all(file_name)
            data.append(item)
            FileHelper.write_all(file_name, data)

    # cập nhật 1 item theo id (tìm → sửa → ghi lại)
    @staticmethod
    def update_item(file_name: str, item_id: int, updated: dict) -> bool:
        lock = FileHelper._get_lock(file_name)
        with lock:
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
        lock = FileHelper._get_lock(file_name)
        with lock:
            data = FileHelper.read_all(file_name)
            new_data = [item for item in data if item["id"] != item_id]
            if len(new_data) == len(data):
                return False  # không tìm thấy, không xóa được
            FileHelper.write_all(file_name, new_data)
            return True

    # ghi đè toàn bộ danh sách 1 cách an toàn (dùng khi controller tự đọc,
    # sửa nhiều phần tử trong list rồi cần lưu lại nguyên khối, ví dụ update_contract)
    @staticmethod
    def write_all_safe(file_name: str, data: list):
        lock = FileHelper._get_lock(file_name)
        with lock:
            FileHelper.write_all(file_name, data)

    # lấy id lớn nhất hiện có trong file để tự tăng ID đúng khi khởi động
    @staticmethod
    def get_max_id(file_name: str) -> int:
        data = FileHelper.read_all(file_name)
        if not data:
            return 0
        return max(item.get("id", 0) for item in data)