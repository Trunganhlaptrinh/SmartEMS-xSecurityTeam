#  SmartEMS — Employee Management System

> Hệ thống quản lý nhân viên thông minh với các chức năng vippro

---

##  Yêu cầu hệ thống

| Công cụ | Phiên bản | Ghi chú |
|---------|-----------|---------|
| Python  | 3.8 trở lên | [Tải tại python.org](https://www.python.org/downloads/) |
| pip     | Đi kèm Python | Tự động cài khi cài Python |

---

## ⚙️ Cài đặt

### Bước 1 — Tải dự án

**Cách 1 — Dùng Git:**
```bash
git clone https://github.com/Trunganhlaptrinh/SmartEMS-xSecurityTeam.git
cd SmartEMS-xSecurityTeam
```

**Cách 2 — Tải file ZIP:**
- Truy cập repository trên GitHub
- Nhấn **Code → Download ZIP**
- Giải nén file ZIP vào thư mục mong muốn

---

### Bước 2 — Cài đặt Python *(nếu chưa có)*

<details>
<summary>🪟 Windows</summary>

1. Tải Python từ [python.org/downloads](https://www.python.org/downloads/)
2. Chạy file cài đặt
3. ⚠️ **QUAN TRỌNG:** Đánh dấu chọn **"Add Python to PATH"**
4. Nhấn **Install Now**

</details>

<details>
<summary>🍎 macOS</summary>

```bash
brew install python
```

</details>

<details>
<summary>🐧 Linux (Ubuntu/Debian)</summary>

```bash
sudo apt update
sudo apt install python3 python3-pip
```

</details>

---

### Bước 3 — Cài đặt thư viện

```bash
pip install -r requirements.txt
```

> 💡 Nếu gặp lỗi, thử: `pip3 install -r requirements.txt`

---

### Bước 4 — Kiểm tra cài đặt

```bash
python --version
pip --version
```

---

## 🚀 Chạy ứng dụng

**1. Khởi chạy server:**
```bash
python app.py
# hoặc
python3 app.py
```

**2. Truy cập ứng dụng:**

Mở trình duyệt và vào địa chỉ: [http://localhost:5000](http://localhost:5000)

**3. Dừng ứng dụng:**

Nhấn `Ctrl + C` trong terminal.

---

## 🔑 Tài khoản mặc định

| Vai trò | Username | Password  |
|---------|----------|-----------|
| Admin   | `admin`  | `admin123` |
| User   | `test`  | `123456` |

> ⚠️ Tài khoản Admin được tự động tạo khi khởi chạy lần đầu. **Vui lòng đổi mật khẩu sau khi đăng nhập.**

---

## 📖 Hướng dẫn sử dụng

### Đăng nhập

1. Truy cập [http://localhost:5000](http://localhost:5000)
2. Nhập **Username** và **Password**
3. Nhấn **"Đăng nhập"**


Trải nghiệm vui vẻ :D
