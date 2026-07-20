# Sử dụng base image Python slim gọn nhẹ
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép các tệp yêu cầu thư viện vào container trước (để cache build layer tốt hơn)
COPY requirements.txt .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn dự án vào container
COPY . .

# Mở cổng 5000 trong container
EXPOSE 5000

# Chạy ứng dụng bằng Gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "app:app"]
