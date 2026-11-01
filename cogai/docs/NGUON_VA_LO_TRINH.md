# Đối chiếu Mind-Reframe, Lumina và phần CogAI đã xây

**Cập nhật 22/10/2026 sau đợt phát triển lõi:** tài khoản bền vững, consent theo
mục đích, điều phối, sự kiện an toàn, công cụ expert và adapter nghiên cứu đã
được bổ sung. Các mục “chưa có” bên dưới là nhận định lịch sử của bản nền;
trạng thái hiện hành nằm trong [biên bản bàn giao](BAN_GIAO_2026_10_22.md).
Adapter không đồng nghĩa tái lập đầy đủ phương pháp hoặc kiểm định chuyên môn.

## 1. Đã tìm thấy gì trong nguồn?

Tài khoản được yêu cầu là [Anonymous-EmpathyAI](https://huggingface.co/Anonymous-EmpathyAI). Tên repository thực tế là `Mind-Reframe`, `Mind-Reframe-v2` và `Lumina`.

Mỗi bản được tải 65 tệp nguồn chọn lọc, có revision/hash trong `research/upstream/*/SOURCE_MANIFEST.json`. Không tải hoặc dùng `.env`, lịch sử phản hồi hay log của Space. Không có khóa nào từ Space được dùng để chạy CogAI.

| Tầng | Mã gốc | Chức năng |
|---|---|---|
| UI | `Web/mind-reframe/src/App.tsx` | React/TypeScript; nhập situation/thought, xem phân tích, chọn hướng, đọc reframe, phản hồi |
| Điều phối | `Web/backend/main.py` | FastAPI; init session, detect, analyze, reframe, feedback, save; bản v2/Lumina có instruction_feedback và improve |
| AI core | `ai-core/app` | Provider abstraction, prompt manager, template, cache, middleware và API |
| Prompt | `ai-core/app/core/prompts/templates/DoT.py`, `reframe.py` | Phân tích sự kiện/suy nghĩ; nhận diện pattern; tạo góc nhìn theo nhiều phương pháp; nhận xét/chỉnh sửa |
| Container | `Dockerfile`, `supervisord.conf` | Python container chạy hai tiến trình; web phục vụ frontend đã build sẵn |

So sánh SHA-256 của 65 tệp chọn lọc: **Mind-Reframe-v2 và Lumina chỉ khác ba tệp**: README gốc, `Web/backend/main.py`, `Web/mind-reframe/src/App.tsx`. Do đó phần AI core trong hai snapshot này giống nhau. Kết luận chỉ áp dụng phạm vi tệp được tải, không bao gồm asset, log hoặc lịch sử Git.

README AI core gọi hướng tiếp cận là ReframeBench; giao diện Lumina nhắc CBT-MACR. Thư mục nguồn được tải không có manuscript đầy đủ cho hai tên này. Đánh giá ở đây dựa vào mã thực thi, không coi các dòng `[cite: ...]` trong README/giao diện là trích dẫn khoa học đã được xác minh. Đây cũng không phải mã thực thi CogRAG trong ba bài báo của hồ sơ CogAI.

## 2. Luồng thuật toán gốc

1. Tạo session ID.
2. Nhận tình huống và suy nghĩ.
3. Gọi `dot.analysis`, rồi `dot.detection`.
4. Gọi `dot.thera_rcm` để gợi ý các hướng.
5. Với mỗi hướng được chọn, tạo reframe và gọi supervisor.
6. Người dùng chọn; bản v2/Lumina cho nhận feedback và sinh lại.
7. Ghi phản hồi ra JSONL; API save chỉ in console.

Mô hình được hard-code tại nhiều chỗ là `gpt-4.1`. Có tầng provider khác nhưng điều phối web không tự sử dụng mọi provider theo cấu hình. Không nên hiểu có lớp provider là đã có hệ thống chuyển mô hình hoàn chỉnh.

## 3. Các khoảng trống cụ thể trong mã gốc

| Phát hiện | Vị trí tham chiếu | Ảnh hưởng khi kế thừa |
|---|---|---|
| Session trong dict RAM | `Web/backend/main.py`, `sessions_store` | Mất khi restart; không có cơ sở sở hữu dữ liệu dài hạn |
| Tạo demo session ID tại UI khi init lỗi | `App.tsx`, `initSession` | Giao diện có vẻ bắt đầu được nhưng backend chưa có phiên đó |
| Save chỉ `print` rồi trả thành công | `main.py`, `/api/save` | Người dùng tưởng đã lưu nhưng chưa có record có thể đọc lại |
| Feedback ghi nội dung input/output vào JSONL | `main.py`, `/api/feedback` | Chưa gắn lựa chọn lưu, mã hóa, xuất/xóa hoặc kiểm tra ownership đầy đủ |
| Có `print` tình huống/suy nghĩ và output | `main.py`, analyze/reframe/save | Nội dung nhạy cảm có thể đi vào log |
| CORS `*` kèm credentials | Cả hai FastAPI app | Cần thay bằng chiến lược cùng nguồn/nguồn rõ ràng |
| Dùng `.seconds` kiểm tra hết hạn | `clean_expired_sessions` | Bỏ phần ngày của timedelta; nên dùng epoch hoặc total_seconds |
| Base URL core là localhost:1812, mặc định Settings PORT=8000 | Web backend và `ai-core/app/config.py` | Cần env cấu hình thống nhất; chưa đọc env gốc nên không kết luận Space hiện tại bị lỗi |
| Docker chỉ cài Python, frontend dựa vào dist có sẵn | Dockerfile, mount StaticFiles | Sửa TSX rồi build container có thể vẫn dùng bản dist cũ nếu không build frontend |
| Kết quả tự do được dò bằng từ khóa/regex | `_check_has_distortion`, `_extract_distortion_types` | Dễ sai với phủ định, thay đổi định dạng hoặc nội dung ngoài danh mục |
| Prompt mặc định suy nghĩ là “distorted”, gợi ý core beliefs, yêu cầu tiếng Anh | DoT.py | Có thể gán nhãn vội; không khớp hỗ trợ tiếng Việt và phạm vi tự chăm sóc |
| Supervisor AI chấm các mặt chất lượng | Prompt và API reframe | Không thay thế phân tầng nguy cơ, đánh giá chuyên gia hoặc xác nhận tiếp nhận ca |

Đây là những điểm phù hợp bản demo/nghiên cứu cần được thay đổi khi thành sản phẩm; không phủ nhận giá trị của luồng tái cấu trúc nhóm đã xây.

## 4. Những gì đã kế thừa và thay đổi trong CogAI

| Thành phần | Quyết định |
|---|---|
| React + TypeScript + Vite | Giữ stack, viết lại UI cho hành trình CogAI và ngôn ngữ Việt |
| FastAPI/Python | Giữ stack, gom lõi mới thành một dịch vụ có mô đun; không cần HTTP tự gọi qua hai port cho mỗi bước |
| CBT/ACT/CFT prompt | Sao chép tài sản gốc có ghi nguồn, dùng trực tiếp trong live |
| DoT | Giữ ý tưởng tách fact/interpretation/evidence; không buộc có méo mó hoặc suy ra core beliefs |
| Supervisor/refinement | Giữ vòng nhận xét và chỉnh sửa, tách khỏi quyết định an toàn |
| Session và feedback | Thay bằng cookie bí danh, SQLite, sở hữu từng record và lựa chọn lưu |
| AI failure | Không dựng niềm tin/cảm xúc giả để làm fallback, không tạo demo session âm thầm |
| Safety | Quy tắc thử nghiệm + model kiểm tra độc lập theo luồng; chặn sinh bình thường khi bước kiểm tra không hoàn tất |
| Sàng lọc và mood | Bổ sung mới để khớp một phần CogAI; bảng hỏi Việt vẫn là bản nháp |
| Docker | Build frontend từ source và backend từ lockfile; Compose nối qua proxy |

## 5. Ranh giới hiện tại với mục tiêu CogAI

Đã có nền cho trò chuyện, bài tập tái cấu trúc, mood, sàng lọc và quyền dữ liệu ở mức bản phát triển. Những phần sau **chưa được triển khai**:

- CogRAG đầy đủ: corpus Việt được phép sử dụng, A(d)/R(d), ba biểu diễn truy hồi, fusion, thẻ đã duyệt và benchmark.
- CARE: appraisal tám trường, predictor, gating, đánh giá cấu hình không dùng hình ảnh.
- EviOCEAN: dữ liệu nhiều phiên, kiểm chứng bằng chứng và cơ chế không kết luận.
- Đầu mối tiếp nhận ca, lịch trực, case management, thông báo có xác nhận, quy trình ngoài giờ.
- Bản dịch bảng hỏi được chọn/kiểm chứng và quy trình chuyên môn.
- Tài khoản dài hạn, RBAC chuyên gia, multi-tenant và báo cáo tổng hợp có chống suy ngược.
- ASR/TTS, MYHealth, ứng dụng native, đồng hồ.
- Giám sát vận hành, backup/restore, quản lý khóa độc lập, xóa dữ liệu dẫn xuất và kiểm định bảo mật trước triển khai ngoài máy.

## 6. Thứ tự phát triển tiếp đề xuất

**Bước 1: chạy bản hiện tại và đánh giá bằng tình huống giả lập của nhóm.** Xác định câu chữ, luồng cảm xúc và kiểu phản hồi muốn có; kiểm tra trải nghiệm công nhân/sinh viên trên điện thoại.

**Bước 2: cấu hình API thật và lập bộ đánh giá tiếng Việt.** Đo chất lượng, lỗi, độ trễ và chi phí theo từng bước. Kiểm thử provider lỗi, model từ chối, JSON sai, nội dung vượt phạm vi và trường hợp nguy cơ. Không coi kiểm thử giả lập là kết quả của model thật.

**Bước 3: hợp tác chuyên gia và hoàn thiện quy trình hỗ trợ.** Duyệt prompt, nội dung, câu hỏi, nguồn liên hệ, vai trò, cách hỏi thêm và tiêu chí dừng. Thay quy tắc thử nghiệm bằng bộ phân tầng đã được đánh giá phù hợp.

**Bước 4: tích hợp CogRAG.** Tạo kho có quyền sử dụng và nội dung được duyệt; chuẩn hóa interface `retrieve(query, appraisal, context)`; so sánh semantic baseline với CogRAG trên tập Việt. Lưu document/card/prompt version theo mỗi phản hồi. Kiểm soát nguồn trước khi đưa vào prompt.

**Bước 5: tài khoản thật và vận hành thí điểm.** Thay phiên 24 giờ bằng xác thực phù hợp; kiểm soát quyền chuyên gia, quy trình tiếp nhận, lưu trữ/đánh giá tác động, backup, quản lý khóa và giám sát. Hoàn tất điều kiện đạo đức, pháp lý và chuyên môn đã nêu trong hồ sơ.

CARE/EviOCEAN, thiết bị và báo cáo tổ chức đi sau khi chứng minh lợi ích bổ sung. Có thể phát triển nghiên cứu song song nhưng chưa cần gắn mọi mô đun vào mỗi tin nhắn của bản đầu.
