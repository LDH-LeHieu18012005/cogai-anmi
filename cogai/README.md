# CogAI — lõi web React + FastAPI

**Nhận diện hiện tại:** trợ lý trò chuyện là **AnMi**, thuộc hệ sinh thái CogAI.
Tên AnMi được dùng trong giao diện, chính sách AI, nhận giọng nói và thông báo
dịch vụ. Hình đại diện SVG thân trắng, mặt tím, màn hình chữ nhật lấy cảm hứng
từ mẫu “Quỷ nhỏ thông thái / Monter Desk AI” người dùng xác nhận. Đây là hình
minh họa trên web; không xác nhận thiết bị vật lý đã tích hợp hay cấu hình bên
trong của mẫu đó. Các ảnh và biên bản cũ có thể vẫn mang tên Mầm/MYHealth.

**Điều chỉnh thoại theo bản thuyết minh:** live dùng nhận dạng
`gpt-4o-transcribe`, một giọng duy nhất `vi-VN-HoaiMyNeural` (Edge, giống video
MYHealth) phát dạng streaming; nguy cơ, appraisal và bản nháp chạy song song,
giữ kiểm tra đầu ra riêng; nhánh `check_in` không còn bị kẹt. Xem
[đối chiếu đề tài và nghiệm thu](docs/DIEU_CHINH_HOI_THOAI_THEO_THUYET_MINH.md).

**Mới:** mục Trò chuyện có nhân vật AnMi hoạt họa, đổi màu/giảm chuyển động và
nút **Bắt đầu nói chuyện** để trao đổi rảnh tay: tự nhận khoảng dừng → tự trả
lời bằng giọng nói → tự nghe lại, hỗ trợ nói chen để ngắt giọng AnMi. Không
cần bấm gửi từng câu. STT/TTS là adapter có cấu
hình/quyền riêng; demo không gọi dịch vụ giọng nói. Xem
[tác nhân và giọng nói](docs/TAC_NHAN_VA_GIONG_NOI.md) để cấu hình trên máy.
Lời nói thêm trong lúc chờ được giữ cục bộ rồi tự gửi tiếp, bỏ phát giọng cũ.
Để cấu hình dịch vụ tương thích OpenAI bằng lời nhắc khóa ẩn, chạy
`node cogai/scripts/setup-voice.mjs`, rồi khởi động lại CogAI. Máy chưa có khóa
thì vẫn ở demo; công cụ không tự xác minh provider.

Bản phát triển chạy cục bộ, kế thừa tài sản prompt Mind-Reframe/Lumina. Mặc định
**demo**: phản hồi mẫu có nhãn, không gọi provider. Chưa kiểm định lâm sàng hoặc
đủ điều kiện vận hành với dữ liệu sức khỏe thật.

## Khởi động

Từ workspace hiện tại:

```powershell
node cogai/scripts/dev.mjs
```

Mở **http://127.0.0.1:5173**; API **http://127.0.0.1:8000/docs**.
Ctrl+C dừng cả hai tiến trình. Không chạy dev cùng Playwright trên hai cổng này.
Launcher kiểm tra cả cổng 5173 và 8000 trước khi khởi động. Nếu báo
`port ... is unavailable (EADDRINUSE)`, còn một dịch vụ đang giữ cổng:
dừng terminal chạy phiên cũ bằng Ctrl+C rồi chạy lại. Không mở thêm launcher
trong terminal thứ hai. Khi cổng bận, launcher không khởi động backend hoặc seed dữ liệu.
Để tự điền khóa vào `backend/.env` rồi chạy OpenAI, dùng
`node cogai/scripts/dev.mjs --live`. Đã bỏ trần yêu cầu/ngày và mức 1.000 token
của chế độ tiết kiệm; dùng mức đầu ra mặc định 1.800 token của adapter.
Giữ kiểm tra an toàn đầu vào/đầu ra, quyền dữ liệu và nhánh hỗ trợ. Launcher
không đọc/ghi `.env`, backend tự nạp khóa; không tự gọi API khi mở trang.
Lệnh cũ `--economy` vẫn là bí danh tương thích, không còn bật trần cũ.
Dependency hiện có trong `backend/.venv` và `frontend/node_modules`; Python bị
mất trên máy đã được thay bằng bản 3.12.10 tại `.tools/python` của workspace.

Trên máy mới, cần Python 3.12/3.13, uv và Node 22.12+:

```powershell
cd cogai/backend
uv sync --frozen --python 3.12
cd ../frontend
npm ci
cd ../..
node cogai/scripts/dev.mjs
```

## Phần đã triển khai

- Cổng robot Ricky/xiaozhi qua OTA + WebSocket/Opus, dùng cùng hội thoại AnMi.
  Chạy `node cogai/scripts/dev.mjs --live --device`; xem
  [hướng dẫn nối robot và trạng thái build firmware](docs/KET_NOI_ROBOT_ANMI.md).

- Phiên khách có đồng ý; nâng cấp thành tài khoản bí danh bền vững mà giữ dữ
  liệu cũ; đăng nhập/đăng xuất/mọi thiết bị, mật khẩu scrypt, cookie HttpOnly.
- Quyền riêng cho lưu lịch sử, AI ngoài, cá nhân hóa, chia sẻ tóm tắt và nhắc
  sàng lọc. Thu hồi dùng revision, xóa dữ liệu dẫn xuất tương ứng, chặn lời gọi
  AI tiếp theo và ghi dữ liệu từ yêu cầu cũ đang chạy.
- Lịch sử/trạng thái lấy từ server, khôi phục khi tải lại/chuyển trang/đăng nhập
  lại; nội dung mã hóa Fernet. Không tin history client gửi. Không lưu thì chỉ
  giữ bộ nhớ tạm của phiên trên server và mất khi logout/hết phiên/restart.
- Bộ điều phối có lắng nghe/làm rõ/nhận diện suy nghĩ/bằng chứng/góc nhìn/hành
  động nhỏ. Người dùng chọn cách đi; Lumina là công cụ tùy chọn. Bài tập và
  chat chia sẻ tình huống, suy nghĩ và nhánh an toàn.
- Sự kiện an toàn chung từ chat/bài tập/phản hồi/mood/sàng lọc; phân biệt high,
  check_in và lỗi dịch vụ unavailable; kiểm tra đầu vào/đầu ra riêng. Reset chat
  không bỏ nhánh hỗ trợ; ý mơ hồ có luồng làm rõ tự báo không nguy hiểm trước mắt.
- PHQ-9/GAD-7 chấm xác định, version/review status rõ; câu hỏi Việt vẫn là bản
  nháp `vi-draft-1`. Nhắc sàng lọc tùy chọn trong ứng dụng.
- Công cụ người thật: quyền expert cấp bằng CLI, tóm tắt do người dùng duyệt,
  hàng đợi/tiếp nhận/xử lý/đóng/không nhận/ngoài giờ. Mặc định chưa cấu hình dịch
  vụ, không tự gửi cảnh báo hoặc tuyên bố đã chuyển ca.
- Migration additive có phiên bản giữ ciphertext cũ; xuất/xóa/thời hạn lưu
  1–365 ngày cho tài khoản. Worker cleanup, backup/restore vào thư mục mới,
  audit không nội dung, health/readiness/metrics, chốt khóa/cookie production.

## Nghiên cứu: adapter và phần thiếu

| Thành phần | Có trong mã | Chưa xác minh/cần bổ sung |
|---|---|---|
| CARE | Schema tám trường đúng PDF, unknown/bằng chứng, cập nhật theo lượt; cổng DoT/social chọn lọc | Predictor huấn luyện, voting, mã tác giả và benchmark tiếng Việt |
| CogRAG | Chuẩn bị A(d)/R(d)/embedding offline, A(q)/R(q) online riêng CARE, cùng encoder ba biểu diễn, fusion, thẻ duyệt/nguồn/version/hash | Kho hợp pháp đã duyệt, cấu hình encoder, chạy model thật và benchmark Việt; chưa có mã tác giả |
| EviOCEAN | Interface bảy nhóm bằng chứng; job nhiều conversation theo quyền; thu hồi/xóa; không kết luận khi thiếu bằng chứng/adapter | Summarizer, extractor, validators high/low và arbitrator đã kiểm chứng; không tạo điểm OCEAN giả |

Không coi các adapter này là tái lập đầy đủ nghiên cứu. Kho tri thức khởi tạo
trống; dữ liệu giả có `development_only=true` và bị loại trong production.
Lexical baseline có nhãn riêng, chỉ bật thủ công cho phát triển. Thiếu encoder
hoặc nguồn phù hợp trả rỗng, không giả có truy hồi thành công.

Kho upstream local chỉ có Mind-Reframe/Mind-Reframe-v2/Lumina. PDF CogRAG dẫn
`https://github.com/CogAI-Lab/CogRAG`; GitHub API công khai trả HTTP 404 khi kiểm
tra ngày 22/10/2026. Chưa thể kết luận repo đã xóa hay là private. Không có mã
CARE/EviOCEAN hoặc trọng số predictor trong workspace.

## Bật AI thật và triển khai

Tại `backend`, sao chép `.env.example` thành `.env` và cấu hình riêng trên máy:

```dotenv
COGAI_MODE=live
COGAI_LLM_API_KEY=<khóa ở máy chủ>
COGAI_LLM_MODEL=<model provider của bạn hỗ trợ>
COGAI_EMBEDDING_MODEL=<để trống nếu chưa dùng semantic retrieval>
```

Không gửi khóa qua hội thoại hay frontend. Adapter dùng Chat Completions JSON
và embeddings tương thích; cần xác minh hợp đồng provider thực tế. `store=false`
trên chat không đồng nghĩa provider không có log vận hành. Che email/điện thoại
chỉ giảm một phần nhận diện, không phải vô danh hoàn toàn.

```powershell
cd cogai
docker compose up --build
```

Docker local mở loopback **http://127.0.0.1:7860**, giữ dữ liệu ở named volume.
Docker Compose đã kiểm tra cấu hình; **chưa build/chạy container vì Docker daemon
trên máy không hoạt động**. Không xóa volume hoặc key khi còn cần dữ liệu.

Hướng dẫn cấp quyền expert, chuẩn bị corpus, production/HTTPS, backup/restore,
cleanup, giám sát và rollback: [VAN_HANH.md](docs/VAN_HANH.md).

## Kiểm thử

Tại backend:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=./test-results/manual-new-run
```

`--basetemp` phải là thư mục riêng trong test-results, pytest có thể tạo lại nó.
Tại frontend:

```powershell
npm run build
npm run test:e2e
```

Playwright dùng Chrome headless và database giả riêng. Trong môi trường kiểm
thử, dịch vụ tiếp nhận được bật chỉ để diễn tập, không phải đối tác thật.
Kết quả và giới hạn: [KIEM_THU.md](docs/KIEM_THU.md).

## Luồng kiểm tra nhanh

Đồng ý lưu → bắt đầu → Tài khoản & quyền dữ liệu → tạo bí danh → chat → chuyển
sang bài tập → tải lại → đăng xuất → đăng nhập → xem lịch sử. Tắt quyền lưu và
kiểm tra nội dung đã xóa. Ghi mood có tín hiệu nguy cơ giả rồi mở bài tập để
kiểm tra nhánh ưu tiên hỗ trợ. Mở Tìm người hỗ trợ để xem trạng thái chưa có
dịch vụ; chỉ dùng chế độ test để diễn tập chuyên gia tiếp nhận.

## Giới hạn còn lại

Chưa có khôi phục mật khẩu/MFA; dùng một API worker vì RAM/locks/hạn mức chưa
chia sẻ nhiều tiến trình. Chưa có worker job bền vững, cảnh báo trực, quản lý
lịch trực tự động, kiểm định bảo mật/hiệu quả chuyên môn, NER tên/địa chỉ, key
rotation hoặc tự áp dụng yêu cầu xóa lên backup cũ. Điều kiện phê duyệt câu hỏi,
nguồn, đối tác và quy trình đánh giá lại nhánh high cần người thật; mã không tự
đánh dấu chúng hoàn tất. Chưa gọi model thật trong đợt xác minh này.

Ngoài phạm vi: MYHealth, ứng dụng native, đồng hồ và dashboard tổ chức. Người
dùng đã mở rộng phạm vi sang STT/TTS web trong đợt tác nhân; xem tài liệu mới.

## Quản trị và dữ liệu mẫu

`node cogai/scripts/dev.mjs --demo-data` chạy với 70 tài khoản tổng hợp (mật khẩu
`cogai2026demo`; `admin`, `expert`, `user`). Xem
[trang quản trị và dữ liệu mẫu](docs/QUAN_TRI_VA_DU_LIEU_MAU.md).

## Nguồn và bàn giao

- [Biên bản triển khai và trạng thái](docs/BAN_GIAO_2026_10_22.md)
- [Đối chiếu mã kế thừa](docs/NGUON_VA_LO_TRINH.md)
- [Tài sản bên thứ ba](THIRD_PARTY_NOTICES.md)
- [Thiết kế và thứ tự triển khai](docs/IMPLEMENTATION_2026_10_22.md)
