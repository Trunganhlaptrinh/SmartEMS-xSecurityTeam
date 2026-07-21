# DISASTER RECOVERY PLAN (DRP)
## Hệ thống SmartEMS – Smart Employee Management Solution

| Thông tin tài liệu | Nội dung |
|---|---|
| Tên hệ thống | SmartEMS (Smart Employee Management Solution) |
| Chuẩn tham chiếu | NIST SP 800-34 Rev.1, ISO 22301 |
| Tài liệu liên quan | BIA_Report.md, BCP_Plan.md, CIRT_Plan.md |
| Nhóm thực hiện | Trung Anh, Phan Hiếu, Doanh, Năng |
| Ngày ban hành | 10/07/2026 |
| Phiên bản | 1.0 |

---

## 1. Mục đích

Disaster Recovery Plan (DRP) tập trung vào việc khôi phục hạ tầng kỹ thuật và dữ liệu của hệ thống SmartEMS sau các sự cố nghiêm trọng (mất máy chủ, hỏng dữ liệu, tấn công mạng). DRP là bước tiếp nối của Business Continuity Plan (BCP), được kích hoạt khi sự cố vượt quá khả năng xử lý bằng các phương án thay thế thủ công và cần khôi phục lại hệ thống ở mức hạ tầng/mã nguồn/dữ liệu.

## 2. Phạm vi khôi phục

DRP bao trùm toàn bộ kiến trúc kỹ thuật của SmartEMS: ứng dụng Flask (app.py, controllers, models, views), cơ sở dữ liệu dạng file JSON, và các tài liệu vận hành liên quan (báo cáo pentest, tài liệu RMF).

## 3. Danh mục thành phần cần khôi phục

| Thành phần | Vị trí lưu trữ | Mức độ ưu tiên | Phương thức khôi phục |
|---|---|---|---|
| Flask Application | `app.py` | **Critical** | Khôi phục từ Git Repository hoặc máy chủ dự phòng |
| Controllers | `controller/*` | High | Đồng bộ lại từ Git và kiểm tra API endpoints |
| Models | `model/*` | High | Khôi phục từ Git, kiểm tra tính tương thích dữ liệu |
| Views (HTML/CSS/JS) | `view/*` | High | Triển khai lại giao diện từ source code |
| Database JSON | `data/*.json` | **Critical** | Restore từ bản backup gần nhất và kiểm tra tính toàn vẹn |
| Employee Data | `employees.json` | **Critical** | Khôi phục từ backup và đối chiếu với hồ sơ nhân sự |
| Contract Data | `contracts.json` | **Critical** | Phục hồi từ bản sao lưu mã hóa hoặc Cloud Storage |
| Salary Data | `salaries.json` | **Critical** | Khôi phục từ backup và xác minh với bộ phận HR |
| Task Data | `tasks.json` | High | Restore từ backup hằng ngày hoặc lịch sử thay đổi |
| Project Data | `projects.json` | High | Đồng bộ lại từ bản sao lưu gần nhất |
| Notification & OTP | `notifications.json`, `otp_codes.json` | Medium | Khởi tạo lại dữ liệu và hủy các OTP cũ |
| Pentest Reports | `pentest/*` | Medium | Khôi phục từ kho lưu trữ tài liệu dự án |
| RMF Documents | `docs/rrm/*` | Medium | Khôi phục từ hệ thống quản lý tài liệu hoặc Git |

## 4. Chiến lược địa điểm dự phòng (Recovery Site Strategy)

| DR Site | Mô tả | Thời gian khôi phục | Áp dụng cho SmartEMS |
|---|---|---|---|
| **Cold Site** | Chỉ có hạ tầng cơ bản, triển khai lại Flask và phục hồi dữ liệu từ bản sao lưu khi xảy ra sự cố | Dài (24–48 giờ) | Phù hợp khi ngân sách hạn chế |
| **Warm Site** | Có sẵn máy chủ dự phòng, môi trường Flask và cơ sở dữ liệu; chỉ cần đồng bộ source code và khôi phục dữ liệu từ backup | Trung bình (2–8 giờ) | **Đề xuất áp dụng cho SmartEMS** |
| **Hot Site** | Hệ thống dự phòng hoạt động song song, đồng bộ dữ liệu gần thời gian thực | Rất ngắn (vài phút) | Không ưu tiên do chi phí cao, vượt nhu cầu hiện tại |

> **Khuyến nghị:** Mô hình **Warm Site** là lựa chọn cân bằng tốt nhất giữa chi phí đầu tư và thời gian khôi phục (2–8 giờ), phù hợp với các mục tiêu RTO đã xác định trong BIA (Authentication: 30 phút – Salary/Contract: 2 giờ).

## 5. Quy trình khôi phục (Recovery Procedure)

1. **Xác nhận sự cố** – Đối chiếu với mã sự cố BCP (BCP01–BCP06) đã được kích hoạt trong BCP_Plan.md.
2. **Cô lập môi trường bị ảnh hưởng** – Ngắt kết nối máy chủ/thành phần bị lỗi khỏi hệ thống production để tránh lan rộng thiệt hại.
3. **Khôi phục hạ tầng ứng dụng** – Triển khai lại `app.py`, `controller/*`, `model/*`, `view/*` từ Git Repository theo đúng phiên bản đã xác thực an toàn.
4. **Khôi phục dữ liệu** – Restore các file JSON (`employees.json`, `contracts.json`, `salaries.json`, `tasks.json`, `projects.json`...) từ bản sao lưu gần nhất theo chính sách backup (7 phiên bản, Local + External + Cloud).
5. **Kiểm tra tính toàn vẹn dữ liệu** – Xác minh dữ liệu khôi phục không bị hỏng định dạng (đặc biệt lưu ý nguy cơ Data Corruption do thiếu file locking đã nêu trong Phần 2 báo cáo rủi ro).
6. **Kiểm thử chức năng** – Kiểm tra các nghiệp vụ Critical (Authentication, Salary, Contract) hoạt động chính xác trước khi đưa hệ thống trở lại phục vụ người dùng.
7. **Thông báo khôi phục hoàn tất** – System Administrator xác nhận hệ thống ổn định, thông báo cho Incident Manager và HR Department để dừng các phương án thay thế trong BCP.
8. **Ghi nhận và cập nhật tài liệu** – Cập nhật Risk Register và tài liệu RMF dựa trên nguyên nhân sự cố thực tế.

## 6. Kế hoạch kiểm thử khôi phục (Recovery Testing)

| Hoạt động kiểm thử | Mục đích | Chu kỳ |
|---|---|---|
| Restore Backup | Kiểm tra khả năng khôi phục dữ liệu từ bản sao lưu | Hàng tháng |
| Disaster Recovery Simulation | Mô phỏng sự cố mất máy chủ hoặc hỏng dữ liệu, đánh giá quy trình DRP | 6 tháng/lần |
| Business Continuity Exercise | Kiểm tra khả năng duy trì các nghiệp vụ quan trọng theo BCP | 1 năm/lần |
| Incident Response Exercise | Diễn tập quy trình ứng cứu của CIRT đối với các tình huống tấn công mạng | 6 tháng/lần |

## 7. Bài học kinh nghiệm (Lessons Learned)

Theo nguyên tắc *Continuous Improvement* của NIST và ISO 22301, mỗi sự cố hoặc cuộc diễn tập đều là cơ hội để hoàn thiện năng lực phục hồi của tổ chức. Sau khi quá trình khôi phục hoàn tất, nhóm phụ trách tiến hành họp đánh giá sau sự cố (Post-Incident Review) nhằm xem xét hiệu quả của các biện pháp đã triển khai, những khó khăn gặp phải và các nội dung cần cải tiến.

Các bài học kinh nghiệm được ghi nhận sẽ được sử dụng để cập nhật quy trình ứng cứu, kế hoạch sao lưu, kế hoạch khôi phục, tài liệu hướng dẫn và chương trình đào tạo. Việc cải tiến liên tục giúp rút ngắn thời gian khôi phục, giảm thiểu thiệt hại và nâng cao khả năng sẵn sàng của SmartEMS trước các sự cố trong tương lai.

## 8. Kết luận

DRP cung cấp quy trình khôi phục hạ tầng và dữ liệu chi tiết, có thứ tự ưu tiên rõ ràng, đảm bảo SmartEMS có thể phục hồi hoạt động trong khung thời gian RTO/RPO đã cam kết tại BIA_Report.md. Kết hợp với BCP_Plan.md (duy trì hoạt động tạm thời) và CIRT_Plan.md (ứng cứu sự cố an ninh), DRP hoàn thiện năng lực ứng phó toàn diện của doanh nghiệp trước các sự cố công nghệ thông tin.

---
*Tài liệu tham chiếu: NIST SP 800-34 Rev.1 – Contingency Planning Guide for Federal Information Systems.*