# BUSINESS CONTINUITY PLAN (BCP)
## Hệ thống SmartEMS – Smart Employee Management Solution
### Xây dựng theo định hướng ISO/IEC 27001:2022 (Annex A – Information Security Continuity)

| Thông tin tài liệu | Nội dung |
|---|---|
| Tên hệ thống | SmartEMS (Smart Employee Management Solution) |
| Chuẩn tham chiếu | ISO/IEC 27001:2022 (Annex A.5.29, A.5.30, A.8.14), NIST SP 800-34 Rev.1 |
| Tài liệu liên quan | BIA_Report.md, DRP_Plan.md, CIRT_Plan.md |
| Nhóm thực hiện | Trung Anh, Phan Hiếu, Doanh, Năng |
| Ngày ban hành | 10/07/2026 |
| Phiên bản | 2.0 (căn chỉnh theo ISO/IEC 27001:2022) |

---

## 1. Mục đích và cách tiếp cận

Business Continuity Plan (BCP) của SmartEMS được xây dựng dựa trên cách tiếp cận **quản lý an toàn thông tin liên tục (Information Security Continuity)** theo ISO/IEC 27001:2022, thay vì theo chuẩn quản lý liên tục kinh doanh chuyên biệt ISO 22301. Điều này có nghĩa là BCP không chỉ tập trung vào việc duy trì hoạt động nghiệp vụ đơn thuần, mà đặt trọng tâm vào việc **duy trì đồng thời cả ba thuộc tính bảo mật (CIA – Confidentiality, Integrity, Availability)** của hệ thống trong suốt quá trình gián đoạn, đúng theo phạm vi của Hệ thống Quản lý An toàn Thông tin (ISMS).

Ba điều khoản Annex A của ISO/IEC 27001:2022 làm nền tảng trực tiếp cho tài liệu này:

| Điều khoản Annex A | Nội dung | Áp dụng trong BCP này |
|---|---|---|
| **A.5.29** – Information security during disruption | Tổ chức phải hoạch định cách duy trì an toàn thông tin ở mức phù hợp trong thời gian gián đoạn | Mục 4 – Kế hoạch duy trì hoạt động có kiểm soát bảo mật |
| **A.5.30** – ICT readiness for business continuity | Mức độ sẵn sàng của hạ tầng CNTT phải được hoạch định, triển khai, duy trì và kiểm thử dựa trên mục tiêu liên tục kinh doanh | Mục 6 – Sẵn sàng hạ tầng CNTT (ICT Readiness) |
| **A.8.14** – Redundancy of information processing facilities | Các phương tiện xử lý thông tin phải được triển khai với mức dự phòng đầy đủ để đáp ứng yêu cầu sẵn sàng | Mục 5 – Chính sách sao lưu và dự phòng |

Cách tiếp cận này đảm bảo BCP của SmartEMS **gắn liền với hệ thống quản lý rủi ro an toàn thông tin (RMF)** đã trình bày ở Phần 1–2 của báo cáo, thay vì là một quy trình quản lý khủng hoảng độc lập.

## 2. Phạm vi áp dụng

BCP áp dụng cho toàn bộ tài sản thông tin và nghiệp vụ cốt lõi của SmartEMS đã được xác định trong Asset Identification (Domain User, System/Application) và Business Impact Analysis: xác thực người dùng, quản lý nhân viên, chấm công, nghỉ phép, tiền lương, hợp đồng, dự án, quản lý công việc (Task) và thông báo nội bộ.

Mục tiêu bảo mật cần duy trì trong suốt thời gian gián đoạn, theo đúng tinh thần A.5.29:

- **Confidentiality** – Dữ liệu nhạy cảm (lương, hợp đồng, PII) không bị lộ ra ngoài phạm vi kiểm soát ngay cả khi chuyển sang phương án thay thế thủ công.
- **Integrity** – Dữ liệu được ghi nhận qua phương án thay thế phải được đối chiếu, xác thực trước khi nhập lại hệ thống chính thức.
- **Availability** – Các nghiệp vụ Critical/High phải có phương án duy trì tối thiểu trong thời gian hệ thống chính ngừng hoạt động.

## 3. Các tình huống giả định (Scenario Assessment)

Các kịch bản dưới đây được kế thừa trực tiếp từ kết quả đánh giá rủi ro tại Phần 2 của báo cáo (các cặp mối đe dọa – lỗ hổng R1–R5), đảm bảo BCP xử lý đúng các rủi ro đã được lượng hóa, không xây dựng tình huống rời rạc:

| Mã sự cố | Mô tả sự cố | Liên kết rủi ro gốc | Mức độ ảnh hưởng |
|---|---|---|---|
| BCP01 | Máy chủ ứng dụng Flask ngừng hoạt động, khiến người dùng không thể truy cập hệ thống | R4 (Data Corruption/Availability) | High |
| BCP02 | Dữ liệu lưu trữ trên JSON bị hỏng, mất hoặc không thể truy xuất | R3, R4 (Race Condition) | **Critical** |
| BCP03 | Hệ thống bị tấn công DoS/DDoS, làm gián đoạn hoặc suy giảm hiệu năng dịch vụ | WAN Domain risk | High |
| BCP04 | Tài khoản quản trị viên (Admin) bị chiếm quyền, dẫn đến nguy cơ thay đổi hoặc đánh cắp dữ liệu | R2 (Insecure Cryptographic Storage) | **Critical** |
| BCP05 | Dữ liệu hợp đồng lao động và thông tin nhân viên bị rò rỉ hoặc truy cập trái phép | R1 (Broken Access Control) | **Critical** |
| BCP06 | Dữ liệu của chức năng Task Management bị mất hoặc không thể khôi phục đầy đủ | R5 (Zip Slip) | Medium |

## 4. Kế hoạch duy trì hoạt động có kiểm soát bảo mật (A.5.29)

Khác với phương án BCP thuần túy vận hành, mỗi phương án thay thế dưới đây đi kèm **yêu cầu kiểm soát bảo mật tối thiểu** phải được đảm bảo trong quá trình sử dụng, theo đúng tinh thần A.5.29:

| Hoạt động | Phương án thay thế | Yêu cầu bảo mật tối thiểu khi vận hành thay thế |
|---|---|---|
| Xác thực người dùng | Tài khoản dự phòng cho quản trị viên → Xác thực tạm thời bằng Email → Emergency Access | Tài khoản dự phòng phải có mật khẩu mạnh riêng biệt, thu hồi ngay sau sự cố; ghi log toàn bộ truy cập khẩn cấp |
| Quản lý lương | Khôi phục từ backup → Excel → Đối chiếu ngân hàng/HR | File Excel xử lý lương phải được mã hóa và giới hạn quyền truy cập chỉ cho HR/Kế toán |
| Quản lý hợp đồng | Bản PDF sao lưu → Cloud (Google Drive/OneDrive) → Bản in cứng | Cloud lưu trữ hợp đồng phải bật xác thực đa yếu tố (MFA) và mã hóa khi lưu trữ |
| Chấm công | Biểu mẫu giấy → Google Forms → Excel/Sheets dùng chung | Google Forms/Sheets giới hạn quyền chỉnh sửa, chỉ Team Leader/HR có quyền ghi |
| Giao nhiệm vụ | Email nội bộ → Microsoft Teams → Zalo/Slack | Không trao đổi thông tin dự án mật qua kênh chat công cộng chưa được phê duyệt |
| Nghỉ phép | Email → Phiếu giấy → Microsoft/Google Forms | Dữ liệu nghỉ phép cá nhân không công khai ngoài phạm vi HR |
| Quản lý dự án | Excel/Sheets → Microsoft Project → Trello/Jira | Không đính kèm tài liệu thiết kế/mã nguồn mật vào công cụ thay thế chưa qua đánh giá bảo mật |
| Quản lý nhân viên | Danh sách sao lưu định kỳ → Excel ngoại tuyến → Backup Cloud | Dữ liệu PII nhân viên chỉ lưu trên thiết bị đã mã hóa ổ đĩa |
| Thông báo nội bộ | Email hàng loạt → Microsoft Teams → Zalo doanh nghiệp | Xác minh danh tính người gửi trước khi phát thông báo hàng loạt (tránh giả mạo/phishing nội bộ) |
| Quản lý Task | Excel theo dõi → Trello/Kanban → Họp giao ban thủ công | Không ghi thông tin xác thực (API key, mật khẩu) vào công cụ theo dõi Task thay thế |

Thứ tự kích hoạt các phương án thay thế tuân theo mức độ ưu tiên RTO/RPO đã xác lập tại **BIA_Report.md**: ưu tiên hàng đầu là Authentication & OTP, tiếp theo là Salary Management và Contract Management.

## 5. Chính sách sao lưu và dự phòng (A.8.14 – Redundancy)

| Chính sách | Giá trị |
|---|---|
| Backup Schedule | Hằng ngày lúc 23:00 |
| Backup Versions | 07 phiên bản gần nhất |
| Backup Location | Local + External + Cloud (đáp ứng nguyên tắc dự phòng theo A.8.14) |
| Mã hóa bản sao lưu | Bắt buộc mã hóa dữ liệu nhạy cảm (lương, hợp đồng, PII) trước khi lưu trữ ngoài hệ thống chính |
| Restore Testing | Kiểm tra khả năng khôi phục định kỳ hàng tháng |

## 6. Sẵn sàng hạ tầng CNTT cho liên tục kinh doanh (A.5.30 – ICT Readiness)

Theo yêu cầu A.5.30, tổ chức phải hoạch định mức độ sẵn sàng CNTT tương ứng với mục tiêu liên tục kinh doanh. Đối với SmartEMS:

- Hạ tầng dự phòng được thiết kế theo mô hình **Warm Site** (chi tiết tại DRP_Plan.md), đảm bảo thời gian khôi phục 2–8 giờ, phù hợp với RTO của các nghiệp vụ Critical.
- Cấu hình tường lửa **Implicit Deny** tại LAN-to-WAN Domain nhằm giảm thiểu bề mặt tấn công trong thời gian hệ thống đang trong trạng thái gián đoạn/khôi phục.
- Rate limiting và giám sát log (Wazuh) được duy trì liên tục kể cả khi vận hành ở chế độ dự phòng, nhằm phát hiện sớm hành vi khai thác lợi dụng thời điểm hệ thống suy yếu.

## 7. Vai trò và trách nhiệm (Roles & Responsibilities)

| Vai trò | Trách nhiệm |
|---|---|
| **Incident Manager** | Kích hoạt BCP, điều phối các bộ phận liên quan và giám sát toàn bộ quá trình duy trì hoạt động, đảm bảo các yêu cầu bảo mật tại Mục 4 được tuân thủ |
| **System Administrator** | Duy trì hạ tầng CNTT, đảm bảo tính sẵn sàng của máy chủ, mạng và các dịch vụ quan trọng theo A.5.30 |
| **Security Team** | Điều tra nguyên nhân sự cố, giám sát an toàn thông tin trong suốt quá trình gián đoạn, đảm bảo CIA được duy trì theo A.5.29 |
| **HR Department** | Đảm bảo các hoạt động nhân sự được duy trì liên tục, xử lý dữ liệu PII theo đúng yêu cầu bảo mật tối thiểu tại Mục 4 |
| **Team Leader** | Phân công công việc, theo dõi tiến độ nhóm và báo cáo tình hình hoạt động trong thời gian xảy ra sự cố |

## 8. Quy trình kích hoạt BCP

1. **Phát hiện & báo cáo** – Sự cố được phát hiện qua giám sát hệ thống (Wazuh) hoặc phản ánh từ người dùng, báo cáo ngay cho Incident Manager.
2. **Đánh giá mức độ & tác động bảo mật** – Incident Manager phối hợp Security Team xác định mã sự cố (BCP01–BCP06), mức độ ảnh hưởng và thuộc tính CIA bị tác động.
3. **Kích hoạt phương án thay thế có kiểm soát** – Triển khai phương án thay thế tương ứng theo Mục 4, đồng thời áp dụng ngay yêu cầu bảo mật tối thiểu đi kèm.
4. **Truyền thông nội bộ có xác thực** – HR Department thông báo đến nhân viên, đảm bảo nguồn thông báo được xác thực để tránh giả mạo.
5. **Giám sát và chuyển tiếp sang DRP** – Khi sự cố cần khôi phục hạ tầng/dữ liệu, chuyển giao cho quy trình **Disaster Recovery Plan (DRP_Plan.md)**.
6. **Khôi phục hoạt động bình thường** – Sau khi hệ thống được khôi phục, dừng phương án thay thế, đối soát dữ liệu và thu hồi các quyền truy cập khẩn cấp đã cấp tạm thời.
7. **Đánh giá tuân thủ ISMS** – Ghi nhận sự cố vào hồ sơ ISMS, đánh giá xem việc xử lý có tuân thủ đầy đủ các điều khoản A.5.29/A.5.30/A.8.14 hay không, làm đầu vào cho chu trình cải tiến liên tục (PDCA) của ISO/IEC 27001.

## 9. Kiểm thử và cải tiến liên tục

Theo nguyên tắc PDCA (Plan – Do – Check – Act) của ISO/IEC 27001, BCP phải được kiểm thử định kỳ và cải tiến dựa trên kết quả thực tế:

| Hoạt động | Mục đích | Chu kỳ |
|---|---|---|
| Diễn tập kích hoạt phương án thay thế | Kiểm tra tính khả thi và mức độ tuân thủ bảo mật của các phương án tại Mục 4 | 6 tháng/lần |
| Đánh giá nội bộ ISMS liên quan đến A.5.29/A.5.30/A.8.14 | Xác nhận BCP còn phù hợp với phạm vi ISMS hiện hành | 1 năm/lần (theo chu kỳ audit nội bộ ISO 27001) |
| Restore Testing | Kiểm tra khả năng khôi phục dữ liệu từ bản sao lưu | Hàng tháng |

## 10. Kết luận

Business Continuity Plan của SmartEMS được xây dựng theo định hướng **ISO/IEC 27001:2022**, đặt an toàn thông tin (CIA) làm trục xuyên suốt thay vì chỉ tập trung vào tính liên tục vận hành đơn thuần. Việc gắn kết trực tiếp với các điều khoản A.5.29 (An toàn thông tin trong gián đoạn), A.5.30 (Sẵn sàng CNTT) và A.8.14 (Dự phòng phương tiện xử lý thông tin) giúp BCP trở thành một phần tích hợp của Hệ thống Quản lý An toàn Thông tin (ISMS), thay vì một quy trình quản lý khủng hoảng tách biệt. Kế hoạch này phối hợp chặt chẽ với **BIA_Report.md** (xác định ưu tiên khôi phục) và **DRP_Plan.md** (khôi phục hạ tầng/dữ liệu) để hình thành năng lực ứng phó toàn diện, đồng thời tuân thủ chu trình cải tiến liên tục PDCA của ISO/IEC 27001.

---
*Tài liệu tham chiếu: ISO/IEC 27001:2022 – Information security management systems — Requirements (Annex A.5.29, A.5.30, A.8.14); NIST SP 800-34 Rev.1.*