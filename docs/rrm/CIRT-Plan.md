# COMPUTER INCIDENT RESPONSE TEAM (CIRT) PLAN
## Hệ thống SmartEMS – Smart Employee Management Solution

| Thông tin tài liệu | Nội dung |
|---|---|
| Tên hệ thống | SmartEMS (Smart Employee Management Solution) |
| Chuẩn tham chiếu | NIST SP 800-61 Rev.2 (Computer Security Incident Handling Guide) |
| Tài liệu liên quan | BIA_Report.md, BCP_Plan.md, DRP_Plan.md |
| Nhóm thực hiện | Trung Anh, Phan Hiếu, Doanh, Năng |
| Ngày ban hành | 10/07/2026 |
| Phiên bản | 1.0 |

---

## 1. Mục đích

Kế hoạch xây dựng Computer Incident Response Team (CIRT) nhằm đảm bảo khả năng phát hiện, phản ứng và phục hồi nhanh chóng trước các sự cố an toàn thông tin xảy ra trên hệ thống SmartEMS, đặc biệt là các lỗ hổng nghiêm trọng đã được xác định trong quá trình đánh giá rủi ro (Broken Access Control, Insecure Cryptographic Storage, Race Condition, Zip Slip).

## 2. Cơ cấu đội CIRT (Team Structure)

| Vai trò | Nhiệm vụ |
|---|---|
| **CIRT Leader** | Điều phối hoạt động ứng cứu, phân công nhiệm vụ và báo cáo tình hình sự cố lên ban quản trị |
| **Security Analyst** | Phân tích log, thu thập bằng chứng số (digital evidence) và xác định nguyên nhân gốc sự cố |
| **System Administrator** | Cô lập, khôi phục hệ thống và đảm bảo dịch vụ hoạt động ổn định trở lại |
| **Developer** | Khắc phục lỗ hổng, rà soát mã nguồn và triển khai bản vá (patch) |
| **HR Representative** | Thông báo tới nhân viên và hỗ trợ các hoạt động liên quan đến nhân sự trong thời gian xảy ra sự cố |

## 3. Quy trình ứng cứu sự cố (Incident Response Process)

Quy trình được xây dựng theo mô hình 6 giai đoạn chuẩn của NIST SP 800-61:

| Giai đoạn | Hoạt động |
|---|---|
| **1. Preparation** | Chuẩn bị chính sách bảo mật, đội CIRT, tài liệu RMF, kế hoạch BCP/DRP, hệ thống backup và các công cụ giám sát (Burp Suite, Wireshark, Wazuh, Nmap) |
| **2. Detection & Analysis** | Phát hiện sự cố, phân tích log, xác định phạm vi ảnh hưởng và thu thập bằng chứng |
| **3. Containment** | Khóa tài khoản bị ảnh hưởng, chặn IP độc hại, cô lập dịch vụ hoặc máy chủ để ngăn sự cố lan rộng |
| **4. Eradication** | Loại bỏ nguyên nhân gốc bằng cách vá lỗ hổng, cập nhật hệ thống, rà soát mã nguồn và thay đổi thông tin xác thực nếu cần |
| **5. Recovery** | Khôi phục dữ liệu từ backup theo quy trình DRP_Plan.md, kiểm tra tính toàn vẹn và đưa hệ thống trở lại hoạt động, tiếp tục giám sát |
| **6. Lessons Learned** | Đánh giá sau sự cố, phân tích nguyên nhân gốc, cập nhật Risk Register, tài liệu RMF, BCP/DRP và cải thiện quy trình ứng cứu |

## 4. Phân loại mức độ ưu tiên xử lý sự cố

| Mức độ | Ví dụ điển hình | Mục tiêu xử lý |
|---|---|---|
| **Critical** | Mất dữ liệu, hệ thống ngừng hoạt động, tài khoản Admin bị chiếm quyền | Xử lý ngay lập tức |
| **High** | Broken Access Control, rò rỉ dữ liệu, tấn công DoS | Ưu tiên xử lý trong thời gian ngắn |
| **Medium** | Lỗi chức năng, Race Condition, OTP bất thường | Xử lý theo kế hoạch |
| **Low** | Lỗi giao diện, cảnh báo không ảnh hưởng bảo mật | Theo dõi và khắc phục khi phù hợp |

## 5. Liên kết với các lỗ hổng đã xác định

Đội CIRT cần đặc biệt chú trọng giám sát và ứng cứu đối với nhóm lỗ hổng Critical/High đã được xác định trong quá trình đánh giá rủi ro của SmartEMS:

- **R1 – Broken Access Control (BOLA/IDOR)** trên API quản lý file dự án → nguy cơ rò rỉ mã nguồn và tài liệu thiết kế mật.
- **R2 – Insecure Cryptographic Storage** (SHA-256 không salt) → nguy cơ chiếm quyền tài khoản qua brute-force/rainbow table.
- **R3/R4 – Race Condition** trong tính năng Shop và ghi dữ liệu JSON đồng thời → nguy cơ gian lận dữ liệu và hỏng cấu trúc file.
- **R5 – Zip Slip** khi giải nén file ZIP dự án → nguy cơ ghi đè file cấu hình hệ thống máy chủ.

Khi phát hiện dấu hiệu khai thác các lỗ hổng trên, CIRT áp dụng ngay quy trình Containment (khóa tài khoản/API liên quan) trước khi tiến hành Eradication (vá lỗ hổng theo các biện pháp kiểm soát đã đề xuất).

## 6. Công cụ hỗ trợ ứng cứu

| Công cụ | Mục đích sử dụng |
|---|---|
| Burp Suite | Phân tích và kiểm thử lỗ hổng web/API |
| Wireshark | Giám sát và phân tích lưu lượng mạng |
| Wazuh | Giám sát log tập trung, phát hiện bất thường (SIEM) |
| Nmap | Rà quét cổng dịch vụ, phát hiện dấu vết xâm nhập |

## 7. Kết luận

Việc xây dựng CIRT giúp SmartEMS hình thành quy trình ứng cứu sự cố thống nhất, từ phát hiện, ngăn chặn, xử lý đến khôi phục sau sự cố. Hoạt động đánh giá sau sự cố (Lessons Learned) và cải tiến liên tục góp phần nâng cao năng lực bảo vệ hệ thống, rút ngắn thời gian phản ứng và giảm thiểu rủi ro trong các lần vận hành tiếp theo. CIRT hoạt động phối hợp chặt chẽ với BCP_Plan.md (duy trì hoạt động) và DRP_Plan.md (khôi phục hạ tầng/dữ liệu) để tạo thành một hệ thống ứng phó sự cố toàn diện cho doanh nghiệp.

---
*Tài liệu tham chiếu: NIST SP 800-61 Rev.2 – Computer Security Incident Handling Guide.*