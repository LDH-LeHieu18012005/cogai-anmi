# Đối chiếu sơ đồ CogAI và kế hoạch hoàn thiện

**Trạng thái sau triển khai 22/10/2026:** xem [bàn giao lõi web](BAN_GIAO_2026_10_22.md)
và [kết quả kiểm thử](KIEM_THU.md). Ma trận bên dưới giữ làm mốc trước triển khai;
không dùng nó làm danh sách chức năng hiện hành. Các điều kiện chuyên môn,
nguồn dữ liệu, mã nghiên cứu và đối tác vẫn cần xác nhận riêng.

Ngày: 22/10/2026. Đối chiếu mã hiện tại với các sơ đồ đã đọc trong `Hinh anh CogAI`, đặc biệt Hình 1, 2, 4 và 9. Đây là kế hoạch triển khai, không phải xác nhận các thành phần đã được xây hoặc kiểm định.

Cập nhật sau đợt triển khai bộ nhớ: server đã quản lý ngữ cảnh chat tối đa 12 lượt, bỏ qua history do client gửi, có API khôi phục/reset và giao diện tải lại khi mở Chat. Phiên đồng ý lưu đọc từ record mã hóa; phiên không lưu dùng RAM và mất sau restart. Chưa có tài khoản dài hạn, bộ nhớ nhiều phiên, appraisal hay điều phối CogRAG. Các mô tả thiếu bộ nhớ bên dưới phản ánh thời điểm lập kế hoạch trước cập nhật này.

## 1. Kết luận kỹ thuật

Bản hiện tại là nền web và bài tập tái cấu trúc kế thừa Lumina. Để khớp hệ sinh thái trong hình, cần bổ sung bộ điều phối hội thoại, bộ nhớ dài hạn có quyền, CARE/CogRAG/EviOCEAN, quản lý sự kiện an toàn/chuyển tuyến, các kênh và hệ thống vận hành.

Chỉ thêm API key sẽ kích hoạt các lời gọi AI đã viết; không tự bổ sung các mô đun còn thiếu.

## 2. Ma trận thiếu hụt

| Thành phần trong hình | Hiện tại | Cần hoàn thiện |
|---|---|---|
| Cổng vào chung | Web gọi FastAPI | Chuẩn hóa kênh, thiết bị, user/conversation/message ID, quyền và chống gửi lặp |
| Đồng ý dữ liệu | Lựa chọn theo phiên | Lựa chọn riêng cho lịch sử, âm thanh, đồng hồ, tính cách, chia sẻ ca; phiên bản và thu hồi |
| Tài khoản chung | Cookie phiên 24 giờ | Danh tính bí danh bền vững, đăng nhập/khôi phục, liên kết thiết bị, phân quyền |
| Giảm thông tin nhận diện | Regex email/số điện thoại | Tên/địa chỉ/ngữ cảnh, kiểm tra chất lượng; xử lý riêng đường đi âm thanh trước ASR ngoài |
| Phân tầng nguy cơ | Quy tắc + lời gọi model riêng trong live | Chính sách mức nguy cơ, đánh giá tiếng Việt, cập nhật theo lượt, trạng thái chưa rõ/lỗi dịch vụ |
| An toàn trên mọi đầu vào | Chat/reframe có kiểm tra; mood dùng quy tắc; mục 9 có cờ | Bộ sự kiện chung cho chat, mood, screening, ASR và phản hồi bài tập |
| Appraisal | Chưa có schema CARE | Tám trường, bằng chứng/độ không chắc chắn, phiên bản và cập nhật qua hội thoại |
| CogRAG | Chưa có | Pipeline corpus, A(d)/R(d), ba biểu diễn, fusion, thẻ được duyệt và đánh giá truy hồi |
| Phản hồi hội thoại | Chat hỗ trợ riêng, reframe riêng | Máy trạng thái hội thoại quyết định khi hỏi thêm, khi đề nghị bài tập, khi dừng để ưu tiên hỗ trợ |
| Kiểm tra đầu ra | Model check trong live | Quy tắc theo phạm vi + kiểm tra bằng chứng/nguồn; đồng nhất chữ, streaming và TTS |
| Bộ nhớ | Record mã hóa theo phiên | Conversation state, lịch sử xác thực từ server, tóm tắt có nguồn, liên tục giữa thiết bị |
| Sàng lọc | Điểm và câu hỏi Việt nháp | Bản câu hỏi được duyệt, lịch nhắc có đồng ý, theo dõi theo thời gian và xử lý kết quả |
| CARE đầy đủ | Chưa có | Gating, predictor, nhãn cảm xúc, cấu hình chữ/giọng nói và benchmark Việt |
| EviOCEAN | Chưa có | Bằng chứng nhiều phiên, khả năng không kết luận, chạy nền, xem/xóa/tắt cá nhân hóa |
| Chuyển tuyến | Màn hình và liên hệ cấu hình | Đối tác thật, tạo yêu cầu có quyền, xác nhận tiếp nhận, ngoài giờ, thất bại và nhật ký trách nhiệm |
| Giọng nói/MYHealth | Chưa nối | ASR/TTS, xác thực thiết bị, nối lại mạng, hủy audio khi đổi nhánh, biểu cảm phù hợp |
| App/đồng hồ | Chưa có | App dùng cùng API; quyền HealthKit/Health Connect, thời điểm, nguồn và chất lượng tín hiệu |
| Tổ chức | Chưa có | Tách tenant, báo cáo tổng hợp, ngưỡng nhóm và chống suy ngược; không mở hội thoại/tính cách |
| Vận hành | Có Docker/Compose | TLS, bí mật, quản lý khóa tách biệt, backup/restore, cảnh báo, giám sát và rollback |

## 3. Luồng xử lý đích

1. Nhận yêu cầu từ kênh, xác thực user/thiết bị/quyền, gắn message ID và chống gửi lặp.
2. Lấy ngữ cảnh được phép từ server; không coi history do client gửi là lịch sử có thẩm quyền.
3. Chuẩn hóa và giảm thông tin nhận diện trước từng dịch vụ ngoài; bảo toàn ý nghĩa liên quan tới nguy cơ.
4. Đánh giá nguy cơ. Có thể tính appraisal/truy hồi song song để giảm chờ nhưng chưa phát nội dung thông thường trước khi có quyết định an toàn.
5. Nếu cần ưu tiên hỗ trợ: dừng luồng tái cấu trúc, dùng nội dung được duyệt, hiện hành động phù hợp, ghi sự kiện và tạo yêu cầu tiếp nhận theo quyền/quy trình đã xác lập. Không giả định hiển thị liên hệ đồng nghĩa người thật đã nhận.
6. Nếu được tiếp tục: trích xuất/cập nhật appraisal, tạo biểu diễn truy vấn và truy hồi tài liệu/thẻ phù hợp từ kho đã duyệt.
7. Bộ điều phối chọn bước: lắng nghe, làm rõ, xem bằng chứng, thử góc nhìn hoặc hành động nhỏ. Không ép mỗi tin nhắn đi hết bài tập CBT.
8. Sinh phản hồi dựa trên ngữ cảnh và nguồn; kiểm tra trước khi gửi chữ hoặc âm thanh.
9. Lưu theo quyền, ghi nguồn/thẻ/phiên bản, độ trễ, chi phí và kết quả kiểm tra; tránh lưu nội dung nhạy cảm trong log hạ tầng.
10. CARE đầy đủ/EviOCEAN và tác vụ nhắc chạy có chọn lọc hoặc nền; kết quả tính cách không được phép hạ mức ưu tiên an toàn.

Đây là luồng có điều kiện: mọi tin nhắn đi qua kiểm tra cần thiết, nhưng không phải tin nào cũng cần tái cấu trúc hay gọi mọi tác tử.

## 4. Thay đổi cụ thể trong code

- `app/main.py`: chuyển từ gọi trực tiếp `ai.chat`/`ai.reframe` sang dịch vụ điều phối chung; chuẩn hóa xử lý sự kiện từ các tính năng.
- `app/ai.py`: tách adapter mô hình khỏi chính sách; thêm appraisal/retrieval/dialogue/output service. Tái sử dụng phần tạo góc nhìn Lumina như công cụ được điều phối gọi khi thích hợp.
- `app/storage.py`: bổ sung schema có migration; tách user khỏi session đăng nhập và conversation; không gắn toàn bộ hồ sơ dài hạn vào phiên tự xóa 24 giờ.
- `app/models.py`: thêm các hợp đồng AppraisalState, ConversationState, RetrievalResult, RiskEvent, Referral, Device và ConsentScope.
- `app/safety.py`: phát triển thành bộ chính sách có phiên bản và tập đánh giá; tránh chỉ bổ sung ngày càng nhiều regex rồi coi là hoàn tất.
- `frontend/src/App.tsx`: tách màn hình/thành phần; bảo toàn trạng thái khi điều hướng. Hiện tại chuyển trang làm unmount Chat, nên lịch sử trong state chat mất; nhật ký đã lưu vẫn tồn tại nếu có đồng ý.
- Thêm module quản lý kho tri thức, job nền, công cụ chuyên gia và báo cáo tổ chức với quyền riêng.

Có thể giữ một ứng dụng FastAPI chia module và thêm worker nền. Chưa cần tách mỗi mô đun thành một microservice. Lựa chọn hạ tầng cụ thể cần dựa trên tải và năng lực vận hành.

## 5. Dữ liệu cần có

Các thực thể dự kiến: User, AuthSession, ConsentRecord, Organization, Membership, Device, Conversation, Message, ConversationState, AppraisalState, MoodEntry, Assessment, RiskEvent, Referral, KnowledgeDocument, SkillCard, PersonalityEvidence, PersonalityProfile và AuditEvent.

Kho định danh tách quyền với kho hồ sơ bí danh. Kho vector lưu biểu diễn truy hồi và metadata/nguồn; không thay thế kho giao dịch. Xóa/rút đồng ý phải bao phủ cả tóm tắt, embedding, profile, cache và tác vụ đang chờ theo chính sách được xác lập.

## 6. Thứ tự thực hiện và điều kiện nghiệm thu

| Giai đoạn | Sản phẩm bàn giao | Điều kiện hoàn tất |
|---|---|---|
| A. Lõi liên tục | Tài khoản bí danh, hội thoại server, đồng ý theo phạm vi, điều phối và sự kiện an toàn chung | Đổi trang/đăng nhập lại không mất ngữ cảnh được phép; chặn truy cập chéo; xóa/thu hồi quyền có hiệu lực |
| B. Appraisal và CogRAG | Kho được phép sử dụng, thẻ được duyệt, pipeline offline/online và phản hồi gắn nguồn | Có thể truy vết và so sánh với semantic baseline trên tập Việt tách biệt; xử lý được không có nguồn phù hợp |
| C. Hỗ trợ và sàng lọc | Bảng hỏi được duyệt, lịch nhắc, công cụ người tiếp nhận, trạng thái bàn giao | Diễn tập đủ nhận ca/không nhận/ngoài giờ; cờ từ mục 9 và các kênh vào cùng luồng; quyền xem đúng vai trò |
| D. Đa phương thức và cá nhân hóa | Giọng nói, CARE, EviOCEAN chạy chọn lọc | Đo trên cấu hình thực tế; có trạng thái không đủ bằng chứng; lỗi tác vụ nền không chặn nhánh hỗ trợ |
| E. Các kênh và tổ chức | MYHealth, app, đồng hồ, báo cáo tổng hợp | Chung hồ sơ và chính sách; không lẫn user trên thiết bị dùng chung; tenant không xem chéo; báo cáo không lộ dữ liệu cá nhân |
| F. Triển khai | Máy chủ/TLS, vận hành, khôi phục, bộ đánh giá và thí điểm có giám sát | Có người chịu trách nhiệm, quy trình sự cố/rollback và điều kiện chuyên môn/pháp lý phù hợp trước người dùng thật |

Chuẩn bị cố vấn, đối tác tiếp nhận, dữ liệu và quyền khai thác ngay từ giai đoạn A; không đợi xây xong mã mới tìm người vận hành.

Không gán tỷ lệ hoàn thành hoặc thời hạn chính xác khi chưa có mã các mô đun nghiên cứu, dữ liệu, nhân lực thực tế và đối tác. Thực hiện A–C trước để có lõi web đúng logic; D–E mở rộng lõi đó sang hệ sinh thái.

## 7. Điểm cần chốt lại trong các hình

- Hình 1: nội dung gọi API sau che dữ liệu không đồng nghĩa toàn hệ thống đã vô danh; đường đi audio cần được mô tả riêng.
- Hình 2: “chạy song song” là lựa chọn hiệu năng, phải có chốt an toàn trước phát phản hồi. Streaming chỉ phát phần đã qua kiểm tra phù hợp.
- Hình 4: quyền nhà trường xem hồ sơ/hội thoại/OCEAN trong nguyên mẫu không được mặc nhiên chuyển thành quyền của tổ chức trong CogAI; phải tách vai trò chuyên gia và người mua dịch vụ.
- Hình 9: câu diễn đạt mệt mỏi/muốn dừng cần quy trình làm rõ ngữ cảnh; không coi một ví dụ mơ hồ là quy tắc gán nguy cơ cao cho mọi trường hợp. Hiển thị liên hệ, kết nối và xác nhận tiếp nhận phải là các trạng thái khác nhau.
- Các con số thời gian trong hình là mục tiêu hoặc số đo nghiên cứu, không phải SLA đã xác minh cho bản tích hợp.

Đợt kiểm tra này là đọc mã/đối chiếu thiết kế; không thay đổi mã chạy hay chạy lại các kiểm thử. Kết quả kiểm thử phần mềm trước đó không đo mức độ hoàn chỉnh của hệ sinh thái và không kiểm định chuyên môn.
