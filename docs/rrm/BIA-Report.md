# BUSINESS IMPACT ANALYSIS (BIA) REPORT
## Hệ thống SmartEMS – Smart Employee Management Solution

| Thông tin tài liệu | Nội dung |
|---|---|
| Tên hệ thống | SmartEMS (Smart Employee Management Solution) |
| Doanh nghiệp | SmartEMS (doanh nghiệp mô phỏng) |
| Phạm vi | Toàn bộ nghiệp vụ vận hành trên nền tảng SmartEMS |
| Chuẩn tham chiếu | NIST SP 800-34 Rev. 1 |
| Nhóm thực hiện | Trung Anh, Phan Hiếu, Doanh, Năng |
| Ngày ban hành | 10/07/2026 |
| Phiên bản | 1.0 |

---

## 1. Mục đích và phạm vi

Business Impact Analysis (BIA) là bước phân tích nền tảng nhằm xác định các chức năng nghiệp vụ quan trọng của hệ thống SmartEMS, đánh giá mức độ ảnh hưởng khi các chức năng này bị gián đoạn, và xác lập các mục tiêu khôi phục (RTO/RPO) làm cơ sở xây dựng Business Continuity Plan (BCP) và Disaster Recovery Plan (DRP).

BIA được thực hiện dựa trên kiến trúc thực tế của hệ thống: ứng dụng web nền tảng Flask, cơ chế lưu trữ dữ liệu bằng file JSON, và các nhóm nghiệp vụ chính: xác thực người dùng, quản lý nhân viên, chấm công, nghỉ phép, tiền lương, hợp đồng, dự án, công việc (Task) và trợ lý AI nội bộ (ChatEMS).

## 2. Phương pháp thực hiện

Quy trình BIA được thực hiện theo 4 bước:

1. **Xác định nghiệp vụ then chốt** – liệt kê toàn bộ chức năng nghiệp vụ của hệ thống SmartEMS.
2. **Đánh giá tác động khi gián đoạn** – phân tích hậu quả về vận hành, tài chính, pháp lý và uy tín nếu từng chức năng ngừng hoạt động.
3. **Xác định mối quan hệ phụ thuộc** – phân tích chuỗi ảnh hưởng dây chuyền giữa các nghiệp vụ.
4. **Thiết lập mục tiêu khôi phục** – xác định RTO (Recovery Time Objective), RPO (Recovery Point Objective) và thứ tự ưu tiên khôi phục.

## 3. Phân tích mức độ ảnh hưởng theo nghiệp vụ

| Nghiệp vụ | Tác động khi ngừng hoạt động | Mức độ ảnh hưởng |
|---|---|---|
| Authentication & OTP | Người dùng không thể xác thực và truy cập hệ thống | **Critical** |
| Salary Management | Ảnh hưởng trực tiếp đến việc tính toán và thanh toán lương | **Critical** |
| Contract Management | Không thể truy cập và quản lý hợp đồng lao động | **Critical** |
| Employee Management | Không thể quản lý thông tin nhân viên | High |
| Attendance Management | Không thể ghi nhận thời gian làm việc | High |
| Task Management | Không thể giao, theo dõi và cập nhật công việc | High |
| Project Management | Ảnh hưởng đến tiến độ triển khai dự án | Medium |
| Notification Service | Không thể gửi thông báo đến người dùng | Medium |
| ChatEMS (AI Assistant) | Người dùng không thể sử dụng chức năng hỗ trợ AI nội bộ | Low |

## 4. Quan hệ phụ thuộc giữa các nghiệp vụ

Việc gián đoạn một chức năng có thể kéo theo ảnh hưởng dây chuyền đến các chức năng phụ thuộc:

- **Authentication & OTP** ngừng hoạt động → toàn bộ người dùng mất khả năng truy cập mọi chức năng khác của hệ thống. Đây là điểm gián đoạn nghiêm trọng nhất (single point of failure).
- **Employee Management** ngừng hoạt động → ảnh hưởng dây chuyền đến chấm công, nghỉ phép, hợp đồng và tiền lương, do các module này phụ thuộc vào dữ liệu hồ sơ nhân viên.
- **Attendance Management** ngừng hoạt động → không thể ghi nhận dữ liệu chấm công, dẫn đến sai lệch khi tính lương.
- **Salary Management** ngừng hoạt động → không thể tính toán và quản lý bảng lương, ảnh hưởng trực tiếp đến quyền lợi nhân viên.
- **Project Management** ngừng hoạt động → không thể giao hoặc theo dõi các Task liên quan đến dự án.
- **Contract Management** ngừng hoạt động → không thể tra cứu hoặc quản lý hợp đồng lao động, phát sinh rủi ro pháp lý.
- **ChatEMS (AI Assistant)** ngừng hoạt động → chỉ ảnh hưởng đến chức năng hỗ trợ, không tác động đến các nghiệp vụ cốt lõi.

## 5. Mục tiêu khôi phục (Recovery Objectives)

| Nghiệp vụ | RTO (Recovery Time Objective) | RPO (Recovery Point Objective) | Thứ tự ưu tiên |
|---|---|---|---|
| Authentication & OTP | 30 phút | 0 phút | 1 |
| Salary Management | 2 giờ | 30 phút | 2 |
| Contract Management | 2 giờ | 15 phút | 3 |
| Attendance Management | 4 giờ | 1 giờ | 4 |
| Task Management | 4 giờ | 30 phút | 5 |
| Leave Management | 8 giờ | 2 giờ | 6 |
| Notification System | 8 giờ | 2 giờ | 7 |
| Employee Management | 8 giờ | 2 giờ | 8 |
| Project Management | 12 giờ | 4 giờ | 9 |
| ChatEMS (AI Assistant) | 12 giờ | 4 giờ | 10 |

> **Ghi chú:** RTO là thời gian tối đa cho phép để khôi phục một nghiệp vụ sau sự cố. RPO là khoảng thời gian dữ liệu tối đa có thể chấp nhận mất mát, tính từ thời điểm sao lưu gần nhất.

## 6. Kết luận và khuyến nghị

Kết quả phân tích BIA cho thấy **Authentication & OTP**, **Salary Management** và **Contract Management** là ba chức năng có mức độ ưu tiên khôi phục cao nhất, do có ảnh hưởng trực tiếp và tức thời đến khả năng vận hành của toàn bộ hệ thống SmartEMS cũng như quyền lợi hợp pháp của nhân viên.

Các chức năng thuộc nhóm **Attendance Management**, **Task Management** và **Employee Management** cần được khôi phục ở giai đoạn tiếp theo nhằm đảm bảo tính liên tục của các nghiệp vụ nhân sự thường nhật.

Kết quả BIA này là đầu vào bắt buộc cho việc xây dựng **Business Continuity Plan (BCP)** và **Disaster Recovery Plan (DRP)**, đảm bảo các kế hoạch ứng phó được thiết kế đúng trọng tâm và đúng mức độ ưu tiên nguồn lực.

---
*Tài liệu tham chiếu: NIST SP 800-34 Rev.1 – Contingency Planning Guide for Federal Information Systems.*