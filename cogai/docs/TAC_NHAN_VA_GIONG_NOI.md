# Tác nhân AnMi và trò chuyện giọng nói

**Cập nhật theo thuyết minh:** [chính sách AnMi, tối ưu độ trễ và tiếng Việt](DIEU_CHINH_HOI_THOAI_THEO_THUYET_MINH.md).
Luồng live rút một lần gọi LLM bằng bộ đánh giá đầu vào nguy cơ + appraisal,
độc lập với sinh phản hồi và kiểm tra đầu ra. Thu mono, bỏ im lặng trước khi
nói, khôi phục 45 giây/đoạn, STT bản đầy đủ, TTS marin/WAV có chỉ dẫn tiếng Việt.

## Mới: cuộc trò chuyện liên tục, rảnh tay

Mục **Nói chuyện cùng AnMi → Bắt đầu nói chuyện** bật một phiên micro sau khi
có đồng ý và cấu hình STT/TTS. Nói tự nhiên; ngừng khoảng 1,1 giây thì hệ thống
tự gửi lời nói, tạo phản hồi đã kiểm tra, đọc thành tiếng rồi tự nghe lại.
Không yêu cầu sửa chữ, bấm gửi hay bấm nghe từng lượt. Khung chữ đóng vai trò
bản chép lời của cuộc trao đổi. Luồng ghi âm thủ công bên dưới vẫn là tùy chọn.

Có nhận tiếng nói cục bộ bằng Web Audio/energy gate: cần khoảng 200 ms tiếng
nói liên tục; một tiếng click ngắn hoặc im lặng không tự tạo lượt gửi. Trong
khi AnMi đang nói, tiếng nói của người dùng đủ rõ khoảng 280 ms sẽ dừng player
và nhận lượt mới. Có nút **Ngắt lời AnMi** dự phòng. Yêu cầu echoCancellation,
noiseSuppression và autoGainControl ở micro; không cam kết khử hết tiếng vọng
trên mọi loa/phòng. Cần thử micro/loa thật; tai nghe giúp tránh thu lại tiếng
của chính AnMi. Đây là ngưỡng năng lượng phát triển, chưa phải VAD ngôn ngữ được
đánh giá. Một khoảng nghỉ trong câu dài có thể bị coi là hết lượt.

Một stream micro giữ trong thời gian cuộc gọi, tự chia đoạn tối đa 45 giây;
đoạn chỉ có im lặng được bỏ tại máy. Ngừng 90 giây không nói sẽ tạm dừng micro.
Micro vẫn dùng để ngắt lời trong lúc phát tiếng. Khi server đang nhận dạng/
sinh/kiểm tra, lời nói thêm được giữ trong RAM tại trình duyệt (một đoạn tối
đa 45 giây/2 MB). Khi lượt trước hoàn tất, bỏ phát âm thanh cũ và tự gửi đoạn
đó tiếp; không tạo hai lượt chat đồng thời. Bộ đệm bao gồm cả khoảng im lặng
trong lúc chờ; khi đầy sẽ báo rõ tạm ngừng ghi để người dùng chờ xử lý rồi nói
tiếp, không nhận thêm âm thanh vào đoạn đó. Phản hồi chữ trước vẫn hiện trong
lịch sử. Khi kết thúc/thu hồi, bộ đệm bị xóa. Khi cần hỗ trợ, chỉ đọc
phản hồi hỗ trợ rồi dừng nghe tự động. Lỗi dịch vụ dừng phiên, không tự retry
để tránh lặp lượt và tính phí ngoài ý muốn.

`/api/voice/turn` điều phối STT → sự kiện an toàn → chat server → kiểm tra →
TTS trong một tác vụ theo chủ sở hữu; trả transcript, reply và audio không lưu.
`/api/voice/cancel` hủy tác vụ đúng owner/turn ID. Kết thúc cuộc gọi, thu hồi
đồng ý, ẩn tab hoặc chuyển trang giải phóng tracks, AudioContext, recorder,
player, object URL và hủy lượt đang xử lý. Nếu chat đã lưu trước khi hủy thì
record đó vẫn theo quyền lưu; không thể rút request mà provider đã nhận.
TTS lỗi vẫn giữ phản hồi chữ và dừng phiên thay vì gửi lại chat.
Phản hồi bình thường qua kênh voice được hướng dẫn nói ngắn 1–2 câu, khoảng
20–45 từ, tối đa
một câu hỏi; vẫn giữ các kiểm tra an toàn. API trả `latency_ms` từng bước
nhận dạng/hội thoại/giọng đọc/tổng để đo dịch vụ thật, không kèm nội dung vào log.

Đây là hội thoại tự động liên tục qua pipeline STT–chat–TTS, **chưa phải
full-duplex audio streaming/WebRTC với model realtime**. Người dùng vẫn chờ
STT, kiểm tra an toàn, model và TTS trước khi nghe; không phát audio chưa qua
luồng kiểm tra để giảm thời gian chờ. Chưa đo độ trễ với provider thật. Browser
phải đang mở và hiện ở foreground, chưa thay thế phần cứng/khả năng hoạt động
nền hoặc offline của thiết bị để bàn.

Phạm vi mới được người dùng mở rộng: cả nhắn tin và nói/nghe. Vì vậy ghi âm,
STT/TTS cho web nằm trong đợt này, thay cho giới hạn “chưa làm voice” của đợt
lõi trước. Không bổ sung MYHealth, app native hoặc đồng hồ.

## Áp dụng AIRI như thế nào?

Nguồn tham khảo chính: https://airi.moeru.ai/ và https://github.com/moeru-ai/airi.
Đã xem README, LICENSE và module `packages/stage-ui/src/stores/modules/speech.ts`.
AIRI dùng kiến trúc nhân vật ảo, renderer, provider giọng nói và quản lý hủy
request/phát tiếng. Mã nguồn AIRI dùng Vue/Pinia; CogAI hiện dùng React/FastAPI.

Đợt này vận dụng cách tách nhân vật, trạng thái hội thoại và xử lý âm thanh;
**không nhúng AIRI, không port toàn bộ engine, không dùng model Live2D/VRM hoặc
nhân vật có sẵn của AIRI**. AnMi là SVG/CSS mới viết cho CogAI: robot AnMi cây,
ba bảng màu, mắt theo trỏ chuột, chớp mắt, chuyển động nhẹ, trạng thái ghi âm/
xử lý/phát tiếng/hỗ trợ. Không gọi đây là nhận diện cảm xúc hoặc lip-sync theo
phoneme; miệng chỉ hoạt họa khi âm thanh thực sự phát. Có giảm chuyển động và
tôn trọng prefers-reduced-motion. Không tải CDN hoặc assets nhân vật bên ngoài.

Tham khảo được ghi trong THIRD_PARTY_NOTICES.md. Chưa sao chép mã AIRI hoặc
nhân vật của họ. Khi bổ sung Live2D/VRM sau này phải kiểm tra giấy phép model,
renderer và runtime riêng, đồng thời tiếp tục đi qua quyền/an toàn của CogAI.

## Luồng nhắn tin và ghi âm thủ công (tùy chọn)

Mở **Trò chuyện** để gặp AnMi. Nhắn tin dùng nguyên `/api/chat`, ngữ cảnh server,
quyền lưu và chính sách an toàn. Nhân vật hiển thị trạng thái tác vụ; không giả
có người thật hoặc gán cảm xúc cho người dùng.

Giọng nói chỉ hoạt động sau khi người dùng đồng ý `voice_processing` và
`external_ai`, rồi cấp quyền micro riêng trong trình duyệt:

1. Bấm micro để ghi; chỉ ghi tối đa 45 giây, giới hạn 2.000.000 byte.
2. Bấm dừng để gửi audio đến backend. Backend kiểm tra phiên/quyền/MIME/header,
   gọi `/audio/transcriptions` của provider đã cấu hình.
3. Chữ nhận dạng hiện trong ô soạn; người dùng được sửa trước khi gửi chat.
   Quy tắc nguy cơ phát sự kiện `voice_transcript` ngay khi có bản chép lời;
   kiểm tra đầu vào đầy đủ tiếp tục chạy khi gửi qua chat.
4. Phản hồi đi qua luồng an toàn hiện tại. Nút **Nghe phản hồi** gọi
   `/api/voice/speak`; server chỉ đọc phản hồi cuối trong ngữ cảnh của chủ sở
   hữu, không nhận text tùy ý từ frontend. Nếu có nhánh hỗ trợ hiện hành thì
   dùng lời hỗ trợ tương ứng. Kiểm tra tín hiệu mới trước khi trả audio.
5. Có thể bật tự đọc phản hồi thường mới. Không tự đọc khi mới mở trang;
   không tự phát phản hồi nguy cơ. Nút dừng ngắt player/request, giải phóng
   object URL; đổi trang hoặc ẩn tab dừng micro/âm thanh.

Âm thanh gốc đi tới dịch vụ STT **trước khi có chữ để che nhận diện**. Điều này
được giải thích trong cửa sổ đồng ý. CogAI không ghi file audio, không lưu audio
vào database và không tự ghi transcript thành nhật ký; chỉ lưu khi người dùng
gửi chat theo quyền lưu. Phản hồi gửi TTS giảm email/số điện thoại bằng cùng
hàm redact; chưa ẩn danh toàn bộ câu chuyện. Chính sách dữ liệu provider cần
được người vận hành xác minh. Quyền được kiểm tra trước/sau request; thu hồi
không thể rút lại audio đã gửi đi.

## Cấu hình trên máy chủ

### Chạy với OpenAI và guardrails

Nếu dịch vụ trả 401, đó là lỗi xác thực, không phải bằng chứng micro hỏng.
Người vận hành tự sao chép nguyên khóa từ OpenAI vào giá trị
`COGAI_LLM_API_KEY` trong `.env`: một dòng, không chèn khoảng trắng/Enter bên
trong, giữ nguyên dấu gạch/ký tự của khóa. Dòng tự xuống hàng do hiển thị trong
editor không phải Enter thật. Không gửi khóa qua chat, log hoặc ảnh chụp màn
hình. Lưu rồi khởi động lại backend; tiến trình đang chạy không tự nạp lại
`.env`. Không cần và không được mở khóa ra công cụ để chẩn đoán.

Chat và voice hiện trả lỗi dịch vụ 503 kèm hướng dẫn an toàn từ mã provider:
401 xác thực, 403 quyền truy cập, 404 endpoint/model, 429 giới hạn/hạn mức.
Không đưa nội dung lỗi gốc từ provider lên UI; không tự thử lại. Trạng thái
“đã cấu hình” chỉ phản ánh có cấu hình, không xác nhận dịch vụ sử dụng được.
Tham khảo [OpenAI error codes](https://developers.openai.com/api/docs/guides/error-codes).

Nếu tự điền khóa trong `backend/.env`, không cần chạy công cụ nhập khóa:

```powershell
node cogai/scripts/dev.mjs --live
```

Launcher không mở/ghi `.env`; tiến trình backend tự nạp khóa. Preset không
chứa bí mật: OpenAI `gpt-4.1-mini`, STT `gpt-4o-transcribe`, TTS
`gpt-4o-mini-tts`/`marin` dạng WAV; dùng mức đầu ra mặc định 1.800 token của adapter,
45 giây mỗi đoạn ghi ở trình duyệt. Tắt phân tích sâu tùy chọn và embedding API;
giữ appraisal văn bản, kiểm tra an toàn đầu vào/đầu ra và truy hồi cục bộ.

Theo yêu cầu mới, đã bỏ trần 12 yêu cầu/ngày và mức 1.000 token của preset
tiết kiệm. `--live` đặt `COGAI_EXTERNAL_DAILY_CALL_LIMIT=0`; ledger cũ được giữ
nguyên nhưng không chặn yêu cầu. Cờ `--economy` cũ là bí danh cho cùng cấu hình,
không còn bật hạn mức cũ. Guardrails vẫn bắt buộc: xác thực/đồng ý, ngữ cảnh
server, kiểm tra đầu vào/đầu ra riêng, ưu tiên nhánh hỗ trợ, giới hạn kích thước
request và tốc độ chống lạm dụng. Lỗi dịch vụ dừng cuộc gọi, không tự retry.
Guardrails an toàn không phải cơ chế giới hạn tiền trên tài khoản OpenAI.

Kiểm tra live ngắn (chỉ chạy khi chủ khóa cho phép), từ `cogai/backend`:
`./.venv/Scripts/python.exe -m app.check_voice`. Tối đa ba yêu cầu: chat128token,
đọc một câu mẫu rồi nhận dạng lại; không lưu audio, không in khóa/nội dung
provider và dừng ngay khi lỗi. Lệnh này không bật trần theo ngày. Không dùng
health check hay kiểm thử tự động để gọi API trả phí. Các kiểm thử pytest
không nạp `.env`, Playwright ép demo và khóa rỗng.

Công cụ cục bộ dành cho dịch vụ tương thích OpenAI, chạy từ workspace:

```powershell
node cogai/scripts/setup-voice.mjs
```

Nhập base URL, tên model chat/STT/TTS, voice ID theo nhà cung cấp, rồi nhập
khóa trong lời nhắc ẩn. Công cụ ghi riêng `backend/.env`, giữ cấu hình dữ liệu
hiện có và chỉ bật live khi nhập đủ; không gửi yêu cầu tới dịch vụ. Không
truyền khóa qua tham số dòng lệnh hoặc cuộc hội thoại. Kiểm tra các cờ có/thiếu
mà không in khóa bằng `node cogai/scripts/setup-voice.mjs status`.
Khởi động lại server sau khi cấu hình. Sau đó mở **Trò chuyện → Bắt đầu nói
chuyện**, đồng ý xử lý âm thanh/AI ngoài và cấp quyền micro.

Máy hiện được chuẩn bị `.env` ở demo, chưa có khóa. Các ID mặc định chỉ là ví
dụ tương thích OpenAI; provider khác phải thay bằng ID họ cung cấp. Ví dụ STT
`gpt-4o-mini-transcribe` là model tương thích cũ, tài liệu OpenAI tại thời điểm
kiểm tra ghi ngừng ngày 26/02/2027; cần kiểm tra lại trước vận hành. Chưa tích
hợp API nhận dạng mới có hợp đồng request khác. Tham khảo tài liệu chính thức
[STT](https://developers.openai.com/api/docs/guides/speech-to-text) và
[TTS](https://developers.openai.com/api/docs/guides/text-to-speech).

Tại `cogai/backend/.env`, dùng khóa backend hiện có, không đưa khóa vào chat,
frontend hoặc log:

```dotenv
COGAI_MODE=live
COGAI_LLM_BASE_URL=https://<provider-compatible>/v1
COGAI_LLM_API_KEY=<secret riêng trên máy>
COGAI_TRANSCRIPTION_MODEL=<model STT provider hỗ trợ>
COGAI_SPEECH_MODEL=<model TTS provider hỗ trợ>
COGAI_SPEECH_VOICE=<voice ID provider hỗ trợ>
```

Provider phải hỗ trợ POST `/audio/transcriptions` (multipart file, model,
language=vi, trả JSON text) và `/audio/speech` (model, voice, input,
response_format=mp3). Không mặc định mọi provider chat đều có hai endpoint này.
Để trống cấu hình thì tính năng tương ứng tắt và giao diện báo rõ. Cấu hình
model/voice thực tế phải được xác minh cùng chất lượng tiếng Việt trước sử dụng.
STT/TTS hiện dùng cùng base URL và khóa với adapter chat; chưa có cấu hình
provider riêng cho từng dịch vụ. HTTPS hoặc localhost cần cho getUserMedia.

Khởi động bằng `node cogai/scripts/dev.mjs` tại workspace. Bản demo vẫn cho
trò chuyện chữ và nhân vật, nhưng không gọi STT/TTS; không có audio mẫu giả làm
phản hồi thật. Chưa có nhận giọng offline hoặc full-duplex audio streaming.
Energy gate và ngắt lời ở chế độ liên tục được mô tả ở đầu tài liệu; ghi âm
thủ công vẫn yêu cầu người dùng dừng từng lượt.

## Kiểm thử và giới hạn

- Backend kiểm tra consent riêng, audio lớn hơn 32 KB, format/body limit,
  không lưu audio, nguy cơ từ transcript, chỉ đọc text server, redaction,
  lỗi provider và thu hồi giữa request.
- Browser dùng micro giả lập và audio silence tự tạo, mock STT/TTS; kiểm tra
  đồng ý → ghi/dừng → xem chữ → gửi chat → phát/dừng → thu hồi.
- Kiểm tra nhân vật/màu/reduced motion, khôi phục chat, nhánh hỗ trợ và màn
  hình 390px. Ảnh ở frontend/test-results/cogai-agent-*.png.
- Chưa gọi nhà cung cấp thật, chưa thử micro thật, chưa đánh giá STT/TTS tiếng
  Việt, độ trễ/chi phí hoặc Safari/iOS. Không coi suite giả lập là chất lượng
  hội thoại giọng nói thật. Metrics token chat chưa bao gồm chi phí audio.
