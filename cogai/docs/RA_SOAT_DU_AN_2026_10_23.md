# Rà soát dự án CogAI — 23/10/2026

## Kết luận

Dự án đã có lõi tài khoản, quyền dữ liệu, bộ nhớ server, hội thoại/CBT, giọng
nói streaming, sàng lọc, hỗ trợ chuyên gia và quản trị. Các phần đã chạy được
có kiểm thử. Tuy nhiên, còn các lỗi an toàn và riêng tư cần sửa trước khi
thử nghiệm với dữ liệu sức khỏe thật. Kiểm thử hiện tại đạt không có nghĩa
là các luồng cạnh tranh, thu hồi và ẩn danh đã được bao phủ đầy đủ.

Đợt này rà soát và tái hiện, không sửa mã chức năng. Không mở `.env`, đọc khóa,
đọc hồ sơ sức khỏe thực tế hoặc gọi API trả phí. Các tái hiện dùng database
tạm và provider giả. Ngưỡng P1 dưới đây nghĩa là cần ưu tiên sửa vì có thể
bỏ sót tín hiệu an toàn hoặc vi phạm quyền dữ liệu; không phải phân loại
lâm sàng người dùng.

## Các lỗi ưu tiên

### 1. P1 — Lọc STT có thể xóa lời tiết lộ nguy cơ

Vị trí: `backend/app/voice.py:29`, `clean_transcript`.

Hàm bỏ cả câu nếu chứa một cụm bị coi là hallucination, bất kể phần còn lại.
Tái hiện: câu tổng hợp “Tôi muốn tự tử, cảm ơn mọi người đã lắng nghe.” có
`rule_risk=high`, nhưng sau lọc trở thành chuỗi rỗng. Lượt thoại trả
`heard:false` trước khi đánh giá an toàn. Đây là lỗi đã tái hiện.

Hướng sửa: bảo toàn tín hiệu nguy cơ trước mọi bước lọc; chỉ loại câu khớp
trọn mẫu rác đã định nghĩa, không xóa cả câu có nội dung người dùng thực sự.
Thêm kiểm thử phủ định, lời trích dẫn, câu nguy cơ trộn với lời cảm ơn.

### 2. P1 — Chat cũ có thể hạ tín hiệu check_in mới

Vị trí: `backend/app/dialogue.py:147`, `final_gate` tại dòng 60;
`backend/app/storage.py:239`.

`resolved` được tính với safety đọc sau khi mô hình hoàn tất, không gắn với
sự kiện mà câu hỏi làm rõ đã nhắm tới. Tái hiện: giữ tác vụ risk của chat cũ,
ghi một sự kiện `check_in` mới, rồi cho tác vụ cũ trả low/source=model.
Chat trả 200 và safety mới bị đổi thành low. Đã tái hiện bằng provider giả.

Hướng sửa: mang ID/phiên bản sự kiện gốc qua tác vụ; chỉ giải quyết đúng
check_in đó bằng thao tác so sánh và cập nhật nguyên tử. Tín hiệu mới phát
sinh trong khi chờ phải giữ nguyên và được hỏi làm rõ riêng.

### 3. P1 — Streaming không kiểm tra lại quyền/nguy cơ khi gửi chunk

Vị trí: `backend/app/voice.py:440`, đặc biệt vòng yield tại dòng 473.

Route kiểm tra quyền lúc bắt đầu, nhưng không kiểm tra trước mỗi phần audio
gửi tiếp. Đã tái hiện: provider giả phát chunk đầu, thu hồi voice_processing,
rồi phát chunk thứ hai. API vẫn trả 200 và body chứa chunk sau thu hồi.
Nhánh streaming cũng thiếu so sánh với sự kiện high/check_in mới như nhánh
buffered đã làm. Audit có kiểm tra revision trước khi bắt đầu body, nên không
khẳng định mọi thu hồi trước chunk đầu đều bị bỏ qua; lỗi sau khi stream bắt
đầu đã được xác nhận.

Hướng sửa: gắn stream với owner, revision, lượt trả lời và phiên bản safety;
kiểm tra lại trước khi gửi từng chunk; đóng producer/prefetch khi không còn
được phép. Không thể thu hồi các byte đã đến trình duyệt/provider trước đó.

### 4. P1 — Retention xóa trạng thái an toàn còn mới

Vị trí: `backend/app/storage.py:336–340`, `cleanup`.

Chỉ cần một record quá hạn, code xóa toàn bộ documents của chủ sở hữu, kể cả
safety mới, safety plan vừa lưu và reminder hiện tại. Tái hiện với một chat
cũ và safety high vừa tạo: trước cleanup có safety, sau cleanup mất safety.
Đây có thể làm mất nhánh ưu tiên hỗ trợ hiện hành.

Hướng sửa: phân biệt trạng thái phụ thuộc dữ liệu nguồn hết hạn với tài liệu
độc lập còn hiệu lực; vô hiệu hóa theo quan hệ nguồn, không xóa toàn bộ owner.
Cần quy định rõ cách giữ hoặc đánh giá lại trạng thái an toàn khi hết hạn.

### 5. P1 — Báo cáo quản trị chưa bảo đảm ngưỡng ẩn danh

Vị trí: `backend/app/admin.py:68`, `:92`, `:135–141`.

Ẩn cả nhóm chỉ áp dụng khi truyền cohort. Với đúng một user và một admin,
report không lọc vẫn trả `suppressed=false`, members=1 và high=1. Phân bố
tâm trạng dùng số record: một người ghi mức một năm lần làm bucket trả 5,
vượt k=5 dù chỉ có một người đóng góp. Đã tái hiện cả hai trường hợp.
Safety/referral counts cũng không được áp dụng suppression theo số người.

Ngoài ra, admin có thể thay đổi thành viên cohort rồi so sánh trung bình của
sáu người với năm người để suy ra người bị tách. Đây là phân tích từ mã,
chưa chạy thực nghiệm riêng. Chỉ kiểm tra kích thước nhóm không đủ bảo vệ
truy vấn có thể thay đổi thành viên theo từng cá nhân.

Hướng sửa: áp dụng ngưỡng với mọi report/bucket, tính người đóng góp khác
nhau; ngăn suy ngược qua các bucket bù và truy vấn chồng lấp. Tách quyền vận
hành tài khoản khỏi quyền báo cáo cho tổ chức, xác định chính sách cohort
ổn định trước khi tuyên bố báo cáo không thể nhận diện cá nhân.

## Các lỗi khác cần xử lý

| Mức | Vị trí | Phát hiện và hệ quả | Bằng chứng |
|---|---|---|---|
| P2 | `backend/app/admin.py:175` và `core_api.py` quản lý cases | Hạ expert thành user không xử lý ca accepted/in_progress đang assigned_to người đó. Người cũ mất quyền, người khác không thấy/không sửa được ca để tiếp nhận. | Rà soát luồng phân quyền/assignment; chưa tái hiện riêng |
| P2 | `frontend/src/useHandsFree.ts:105`, `:152` | `show()` gọi callback trong finally mà không kiểm tra generation/active. Hủy cuộc gọi khi play đang chờ rồi reject có thể đưa reply/risk cũ trở lại sau reset/thu hồi. | Rà soát thứ tự await và cleanup; chưa tái hiện riêng |
| P2 | `backend/app/storage.py:314–327` | Thu hồi screening_reminders chỉ xóa SQLite, không xóa reminder trong RAM của phiên không lưu; bật lại quyền có thể làm reminder cũ hiện lại. | Rà soát nhánh consent/volatile; chưa tái hiện riêng |
| P2 | `frontend/nginx.conf:12` | CSP không cho phép media từ blob, trong khi nghe thủ công và audio fallback dùng object URL. Bản Vite chạy được nhưng Docker/Nginx có thể không phát âm thanh. | Chrome giả lập đúng CSP xác nhận `media-src`, scheme `blob`, bị chặn |

Riêng CSP: cần cho phép đúng nguồn media cần dùng, đồng thời kiểm tra lại
buffering của reverse proxy cho `/api/voice/stream`; không mở rộng CSP toàn
bộ bằng wildcard để xử lý lỗi.

## Đối chiếu các phần đã xây

| Thành phần | Hiện có | Giới hạn thực tế |
|---|---|---|
| Tài khoản, phiên, đồng ý | Bí danh, mật khẩu băm, cookie, phân quyền user/expert/admin, revision thu hồi | Chưa có khôi phục mật khẩu/MFA; lỗi thu hồi streaming cần sửa |
| Bộ nhớ và dữ liệu | Hội thoại server, records/documents mã hóa, xuất/xóa, migration, retention | Cleanup hiện xóa quá rộng; cần kiểm tra key rotation/xóa theo backup |
| Hội thoại/CBT | Pacing theo appraisal và readiness, câu hỏi Socratic, công cụ Lumina, kế hoạch an toàn cá nhân | Cần chuyên gia đánh giá; máy trạng thái/prompt không phải bằng chứng hiệu quả CBT |
| Voice | STT, Edge HoaiMy, NDJSON tiến độ, prefetch/streaming, ngắt lời, VAD cục bộ | Các lỗi STT/stream/cancel nêu trên; VAD năng lượng cần thử thiết bị thật |
| CARE | Tám trường, bằng chứng trích dẫn, gates DoT/distortion/social, giả thuyết có nguồn | Chưa có predictor/voting/đánh giá Việt như nghiên cứu; nội dung phản hồi có thể dùng appraisal từ lượt trước do chạy song song |
| CogRAG | Chuẩn bị corpus, projections, embeddings, fusion, thẻ kế hoạch, ngưỡng khớp | Voice dùng semantic-only; không phải đầy đủ ba biểu diễn cho mọi lượt. Starter là draft/development, chưa được chuyên gia duyệt |
| EviOCEAN | Interface, job theo quyền, nhiều phiên, trạng thái không đủ bằng chứng/thiếu adapter, thu hồi/xóa | Chưa có chuỗi infer/validate/arbitrate được kiểm chứng; chưa có điểm OCEAN thật |
| Sàng lọc/an toàn | PHQ-9/GAD-7 chấm xác định, kiểm tra đầu vào/đầu ra riêng, safety events chung | Bản Việt vẫn có nhãn draft; còn lỗi bảo toàn tín hiệu và xử lý đồng thời |
| Hỗ trợ chuyên gia | Tóm tắt theo quyền, hàng đợi, tiếp nhận và trạng thái xử lý | Cần xử lý chuyển ca khi thay role; đối tác/lịch trực/điều kiện chuyên môn là việc vận hành |
| Quản trị/dữ liệu mẫu | Dashboard, cohort, tài khoản, audit, bộ dữ liệu tổng hợp tách kho | Lỗi ẩn danh quan trọng; dữ liệu mẫu không chứng minh chất lượng/hiệu quả sản phẩm |
| Triển khai | Dockerfiles, Compose production, Nginx, health/readiness, backup/restore/cleanup | Docker daemon không truy cập được trong phiên; chưa chạy container, có lỗi CSP. RAM/locks/prefetch cần thiết kế lại nếu nhiều worker |

## Xác minh đã chạy

- Backend: **111/111 kiểm thử đạt**, 43,11 giây. Một cảnh báo deprecation
  Starlette/httpx testclient. Pytest không nạp `.env` và dùng khóa rỗng/giả.
- Frontend: **TypeScript và Vite build đạt**.
- Browser: **19/20 luồng đạt** trong môi trường riêng 5174/8001. Test chuyên
  gia còn gắn cứng cổng 5173 và đường dẫn database, nên kết quả lỗi ban đầu
  không phải bằng chứng chức năng expert lỗi. Đã chạy lại riêng bản sao test,
  chỉ đổi cổng/database sang kho sạch: **1/1 đạt**. Không gọi đây là một lần
  chạy nguyên trạng toàn bộ 20/20. Harness cũ cũng bị ảnh hưởng bởi ca thử tồn
  trong database; cần bỏ URL/path gắn cứng và tạo dữ liệu sạch từng lượt.
- Test chuyên gia gắn cứng đã tạo một tài khoản tổng hợp `expert-timestamp`
  ở cổng ứng dụng đang mở; đã xác định đúng alias từ trace của test, đăng nhập
  bằng mật khẩu tổng hợp và xóa đúng tài khoản đó. Không sửa tài khoản khác.
- Script tái hiện: `.tools/audit_project_20261023.py`, chạy từ backend bằng
  `.venv/Scripts/python.exe ../../.tools/audit_project_20261023.py`. Xác nhận
  năm trường hợp: STT, retention, report nhóm nhỏ, race check_in, streaming
  sau thu hồi. Chỉ dùng store tạm/provider giả. Có thể còn file SQLite giả
  trong test-results vì khóa file Windows; không phải dữ liệu người dùng.
- CSP được tái hiện bằng trang Chrome trả cùng header Nginx và blob audio;
  nhận securitypolicyviolation `media-src`/`blob`.
- Chưa gọi model thật, thử chất lượng giọng/micro thật, kiểm thử tải, pentest,
  đánh giá mô hình/chuyên môn hoặc chạy container trong đợt rà soát này.

## Thứ tự xử lý đề nghị

1. Bảo toàn lời nguy cơ trong STT và sự kiện check_in mới; thêm kiểm thử hồi quy.
2. Chốt thu hồi/safety cho streaming và loại callback của lượt đã hủy.
3. Sửa retention để bảo toàn tài liệu độc lập và trạng thái an toàn còn hiệu lực.
4. Sửa ẩn danh báo cáo trước khi cấp quyền báo cáo cho tổ chức.
5. Bổ sung chuyển ca khi thay role, xóa reminder trong mọi kho, sửa CSP và harness.
6. Sau khi pass phần mềm mới đánh giá model/voice thật trên bộ tình huống Việt
   đã được duyệt, tách biệt với diễn tập và số liệu tổng hợp mẫu.
