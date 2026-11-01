# Vận hành lõi web CogAI

Đã có tác nhân AnMi và mở rộng STT/TTS cho web theo yêu cầu mới. Cấu hình, quyền
âm thanh, giới hạn và phần AIRI được vận dụng: [tác nhân và giọng nói](TAC_NHAN_VA_GIONG_NOI.md).

## Chạy và kiểm tra cục bộ

Từ thư mục workspace:

```powershell
node cogai/scripts/dev.mjs
```

Mở http://127.0.0.1:5173; health http://127.0.0.1:8000/api/health;
readiness http://127.0.0.1:8000/api/ready. Ctrl+C dừng hai tiến trình.
Mặc định demo, không gọi AI ngoài. Không chạy đồng thời dev và Playwright trên
cùng cổng. Sau khi bắt đầu, vào **Tài khoản & quyền dữ liệu** tạo bí danh để
đăng nhập lại. Phiên khách vẫn hết hạn sau 24 giờ; tài khoản giữ dữ liệu nội dung
mặc định 30 ngày, chọn được 1–365 ngày. Cookie đăng nhập hết hạn sau 24 giờ.

Mật khẩu dùng scrypt với salt riêng, token chỉ lưu hash. Chưa có khôi phục mật
khẩu/MFA. Không dùng dữ liệu sức khỏe thật cho kiểm thử phát triển.

## Cấu hình dịch vụ và bí mật

Tại `cogai/backend`, sao chép `.env.example` thành `.env` trên máy. Đặt
`COGAI_MODE=live`, `COGAI_LLM_API_KEY` và `COGAI_LLM_MODEL` vào tệp riêng hoặc
secret store. Không gửi khóa qua hội thoại, frontend hay log. Nếu cần semantic
retrieval, cấu hình `COGAI_EMBEDDING_MODEL` bằng model mà provider hỗ trợ.
Để trống thì semantic adapter không được kích hoạt; hệ thống trả không có nguồn.

Production yêu cầu `COGAI_ENVIRONMENT=production`, Fernet key riêng trong
`COGAI_ENCRYPTION_KEY`, `COGAI_COOKIE_SECURE=true` và HTTPS do reverse proxy
người vận hành quản lý. Ứng dụng từ chối khởi động nếu thiếu key/cookie secure.
Đặt `COGAI_ALLOWED_ORIGINS` đúng origin HTTPS. Không đưa key vào Docker image.
File `.env.production.example` là mẫu, không tự được Compose nạp; chuyển các
biến cần thiết vào `backend/.env` được bảo vệ hoặc secret injection của host.

```powershell
cd cogai
docker compose -f compose.yaml -f compose.production.yaml config --quiet
docker compose -f compose.yaml -f compose.production.yaml up --build -d
```

Không tự công bố dịch vụ. Cổng web chỉ bind loopback 7860; API không mở cổng ra
host. Chạy **một API worker** ở bản này: khóa AI, hạn mức và bộ nhớ không lưu
dùng RAM của tiến trình. Trước khi scale nhiều worker phải chuyển các thành phần
này sang kho chung, kiểm thử đồng thời và diễn tập thu hồi quyền.

## Chuyên gia và trạng thái tiếp nhận

1. Người tiếp nhận tạo tài khoản bí danh qua giao diện.
2. Người vận hành xác minh vai trò/chuyên môn/quy trình bên ngoài ứng dụng.
3. Tại backend, cấp hoặc rút quyền bằng CLI cục bộ:

```powershell
.\.venv\Scripts\python.exe -m app.operations grant-expert bi-danh
.\.venv\Scripts\python.exe -m app.operations revoke-expert bi-danh
```

Không có API tự nâng quyền. Đăng nhập/tải lại trang để hiện **Tiếp nhận hỗ trợ**.
Chuyên gia chỉ thấy tóm tắt đã chia sẻ, không có quyền đọc nhật ký/chat qua
API người dùng khác. Cần kiểm tra endpoint và quy trình trước cấp quyền thật.

`COGAI_SUPPORT_ACCEPTING=false` mặc định: tạo yêu cầu ở `unavailable`, không
thông báo hoặc hứa có người nhận. Chỉ đặt true sau khi có người chịu trách nhiệm,
lịch trực, quy trình kiểm tra hàng đợi và phương án ngoài giờ thật. `pending`
chưa phải đã chuyển ca. Người nhận phải bấm xác nhận để chuyển `accepted`, sau
đó `in_progress`/`resolved`. Có `declined`, `out_of_hours`, `unavailable` để diễn
tả không tiếp nhận được. Hiện việc phân ca và kiểm tra lịch trực là thủ công;
không có gửi email/SMS hay báo thức trực tự động. Không tự điền liên hệ đối tác.

Người dùng duyệt tóm tắt, đồng ý chia sẻ riêng; có thể rút yêu cầu hoặc quyền
chia sẻ. Việc này xóa tóm tắt khỏi dữ liệu hoạt động/hàng đợi, không thu hồi
những gì người thật đã đọc hoặc sao chép ngoài hệ thống.

## Kho tri thức và nghiên cứu

Kho khởi tạo trống. Nguồn đầu vào JSON là danh sách thẻ có `id`, `text`,
`source`, `version`, `license`, `review_status`, `reviewed_by`,
`development_only`. Không dùng dữ liệu cá nhân hoặc nội dung chưa có quyền gửi
provider cho bước chuẩn bị. `approved` là xác nhận của người vận hành về việc
duyệt thật, không được tự đặt bằng script để hợp thức hóa nội dung mẫu.

```powershell
# Tạo A(d), R(d), embeddings offline; cần cấu hình live + embedding model
.\.venv\Scripts\python.exe -m app.operations prepare-knowledge duong-dan-corpus.json
# Nhập thẻ đã có appraisal/cbt (và vectors/embedding_model nếu semantic)
.\.venv\Scripts\python.exe -m app.operations ingest-knowledge duong-dan-the.json
```

Chuẩn bị tất cả trước rồi mới ghi kho; lỗi không nhập nửa batch. Online tạo
A(q), R(q) riêng, dùng cùng encoder cho ba biểu diễn, fusion 0.5/0.25/0.25.
Đây là trọng số cấu hình ban đầu, chưa được tối ưu/kiểm chứng trên tập Việt.
Nguồn trả kèm id/version/hash và điểm từng thành phần; thẻ draft/withdrawn bị
loại. Dùng `development_only=true` cho dữ liệu giả; production luôn loại mẫu.
`COGAI_KNOWLEDGE_DEVELOPMENT=true` chỉ bật lexical baseline ở môi trường phát
triển khi thiếu encoder, có nhãn rõ; không phải semantic CogRAG.

CARE hiện là adapter văn bản tám trường, có `unknown`, chứng cứ trích nguyên văn
và cổng DoT/social chọn lọc. Chưa có predictor học có giám sát, voting và đánh
giá tiếng Việt của bài báo. EviOCEAN hiện là interface bảy nhóm bằng chứng và
job theo quyền; dưới ba conversation thì thiếu bằng chứng, trên ngưỡng vẫn
`adapter_unavailable`. **Không tạo điểm/tính cách giả.** Job chạy sau chat khi
có quyền hoặc qua nút kiểm tra, chưa phải worker bền vững có retry xuyên restart.
Ngưỡng ba conversation là điều kiện phát triển, không phải ngưỡng bài báo.

## An toàn và giới hạn quyền

Tín hiệu chat, bài tập, phản hồi bài tập, mood và PHQ-9 đi vào sự kiện chung.
`high` dừng bài tập thường; `check_in` hỏi thêm; `unavailable` là lỗi dịch vụ,
không phải kết luận nguy cơ cao. Reset chat không xóa nhánh an toàn. Với ý mơ
hồ, người dùng có thể làm rõ và tự báo không có nguy hiểm trước mắt; cách này
không xóa sự kiện và không cấp chứng nhận an toàn. Nhánh high không tự được
gỡ qua nút làm rõ; cần xây/duyệt quy trình người thật đánh giá lại trước thí điểm.

Quy tắc và câu chữ hỗ trợ vẫn là bản phát triển chưa duyệt chuyên môn. Bảng hỏi
giữ `vi-draft-1`, chấm xác định. Sàng lọc chỉ hiển thị nhắc trong ứng dụng theo
quyền, không gửi thông báo ngoài. Kiểm tra provider và đầu ra độc lập với
supervisor chất lượng Lumina. Che email/số điện thoại chỉ giảm nhận diện một
phần; chưa có NER tên/địa chỉ được đánh giá. Không gọi dữ liệu là đã vô danh.

Thu hồi đồng ý thay revision; kiểm tra lại trước mỗi lần gửi AI kế tiếp và mỗi
lần ghi. Không thể thu hồi request đã gửi provider. Tắt lưu xóa lịch sử/trạng
thái dẫn xuất; nhánh an toàn hiện hành chỉ giữ tạm trong RAM để không vô tình
bỏ qua ưu tiên hỗ trợ ngay trong phiên đó. Không retroactively lưu hội thoại RAM
khi bật lại lưu. Đăng xuất/xóa/hết phiên/restart xóa bộ nhớ tạm.

## Backup, restore và rollback

Tại backend, dùng một đường dẫn snapshot **mới**. Backup SQLite dùng online
backup API nhất quán với WAL, kèm manifest hash/schema/fingerprint key và
snapshot kho tri thức. Không kèm khóa mã hóa; lưu khóa ở nơi riêng có kiểm soát.

```powershell
.\.venv\Scripts\python.exe -m app.operations backup ./backups/snapshot-001.sqlite3
.\.venv\Scripts\python.exe -m app.operations restore ./backups/snapshot-001.sqlite3 ./restored-001
```

Restore chỉ vào thư mục chưa tồn tại, kiểm tra hash/integrity/schema/key trước
copy. Khi dùng key cục bộ dev, restore sao chép key hiện hành vào thư mục mới;
production tiếp tục lấy cùng key từ secret store. Sau restore phải khởi động
kiểm tra trên bản sao, đối chiếu dữ liệu giả/lệnh health rồi mới chuyển
`COGAI_DATA_DIR` sang thư mục mới. Không ghi đè database đang chạy.

Migration hiện là additive, có `PRAGMA user_version`, từ chối schema mới hơn
ứng dụng. Trước nâng cấp: chụp snapshot, lưu bản mã/container tương ứng. Rollback:
dừng dịch vụ, chạy release cũ với **snapshot trước nâng cấp** và đúng key, không
trỏ release cũ vào database đã nâng cấp. Các ghi nhận sau snapshot không có
trong rollback; cần kế hoạch đối soát và tái áp dụng yêu cầu xóa/thu hồi từ sau
snapshot trước khi mở lại quyền truy cập. Chưa có automation replay tombstone
trên backup cũ. Lập lịch backup bằng hệ điều hành và diễn tập khôi phục định kỳ.

## Dọn dữ liệu và giám sát

Worker trong tiến trình dọn mặc định mỗi 60 giây (`COGAI_MAINTENANCE_SECONDS`),
startup và request xác thực cũng dọn. Khi xóa nguồn hết hạn sẽ xóa trạng thái
dẫn xuất liên quan theo chính sách bảo thủ. Chạy thủ công:

```powershell
.\.venv\Scripts\python.exe -m app.operations cleanup
```

Health là liveness; readiness kiểm tra database. `/api/metrics` yêu cầu vai trò
expert hiện tại, trả số lượng request/lỗi/độ trễ/token, không có nội dung hội
thoại. Metrics nằm RAM và reset khi restart, chưa có exporter/cảnh báo ngoài.
Chi phí `cost_usd=null` khi chưa cấu hình cả `COGAI_LLM_INPUT_USD_PER_MILLION`
và `COGAI_LLM_OUTPUT_USD_PER_MILLION`; khi cấu hình là ước tính token chat,
chưa bao gồm embeddings/thuế/các phí provider khác. Đối chiếu hóa đơn thật.

Audit tối thiểu gồm tài khoản/đăng nhập/xuất/thời hạn/đọc hàng đợi/chuyển trạng
thái/cấp vai trò; không ghi text hay khóa. Consent history có revision riêng.
API tắt access log; nginx tắt access log; Compose giới hạn kích thước log.
Chưa có quản lý sự cố/cảnh báo trực, external audit sink hoặc key rotation tự
động. Xóa logic không bảo đảm xóa vật lý trên SSD/WAL hoặc backup. Người vận
hành phải quy định thời hạn backup và cách áp dụng yêu cầu xóa khi restore.
