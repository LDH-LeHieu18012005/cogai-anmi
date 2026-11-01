# Xác minh lõi CogAI — 22/10/2026

**Đợt điều chỉnh thoại theo thuyết minh:** backend 90 kiểm thử đạt, browser 19
luồng đạt, build đạt. Sau bổ sung kiểm tra RIFF/WAV và rút gọn prompt, các test
liên quan chạy lại đạt. Bộ đánh giá đầu vào rút một lần gọi nhưng vẫn tách
khỏi sinh phản hồi và kiểm tra đầu ra; có test high/đầu vào lỗi/đầu ra bị chặn.
Một lượt câu mẫu tổng hợp đã đi qua provider thật thành công: STT 828 ms,
hội thoại/kiểm tra 5.781 ms, giọng đọc 2.516 ms, tổng 9.125 ms; nhận đúng các
từ chính, có WAV, không lỗi. Không có baseline cùng điều kiện, không suy ra
chất lượng trên micro thật hoặc chứng nhận lâm sàng. Không mở `.env` hoặc in
khóa. Xem [đối chiếu đề tài](DIEU_CHINH_HOI_THOAI_THEO_THUYET_MINH.md).

**Cấu hình hiện tại theo yêu cầu mới:** launcher `--live` tắt trần yêu cầu theo
ngày, bỏ mức 1.000 token của preset cũ và dùng đầu ra mặc định 1.800 token.
`--economy` là bí danh tương thích cho cùng cấu hình. Giữ các guardrails an
toàn/quyền và không xóa ledger cũ. Đã chạy lại bộ kiểm thử liên quan đến an
toàn, dịch vụ, voice và hạn mức tùy chọn; đạt. Không gọi API thật hoặc mở `.env`
trong đợt thay đổi này. Các ghi nhận giới hạn tiết kiệm bên dưới là lịch sử.

**Đợt chẩn đoán không nói chuyện được:** một probe được yêu cầu đã dừng ngay
tại chat, một yêu cầu, provider HTTP401; chưa gọi STT/TTS, không retry. Không
mở `.env` hoặc in khóa. Đã sửa thông báo trạng thái cấu hình và chuyển lỗi
xác thực thành thông báo dịch vụ cụ thể, không hiển thị body provider. Thêm
hai test backend chứng minh chat/voice dừng sau một request401, không lộ
marker bí mật; một browser test chứng minh lỗi hiện rõ và tracks micro đóng.
Đạt 85/85 backend tests (15,52 giây), 19/19 Playwright workflows (1,3 phút),
TypeScript/Vite build đạt. Browser dùng giả lập, không phải xác minh micro/loa
thật. Chờ chủ khóa tự cập nhật; chưa xác nhận nói chuyện thật dùng được.

**Các kiểm thử setup trước đây:** gồm sáu test về
hạn mức bền vững, chặn trước HTTP, chia sẻ hạn mức chat/voice, đặt trước đồng
thời không vượt mức, probe tối đa ba yêu cầu và không retry khi lỗi. Sau khi
bổ sung phân loại lỗi probe bằng mã an toàn, sáu test liên quan chạy lại đạt.
Pytest không nạp `.env` người vận hành; Playwright ép demo/khóa rỗng. Không đọc
hoặc in khóa bằng công cụ. Model Settings ẩn khóa khỏi repr.

Đã khởi động dev `--economy` ở localhost:5173/8000: health ok/live, DB ready,
Chrome headless thấy nhân vật và nút bắt đầu nói chuyện; chặn mọi mutation trong
trang thử nên không gọi provider. Một lần thử thật đã được chủ khóa cho phép:
dừng ngay tại chat, `requests_attempted=1`, lỗi `provider_unavailable_or_invalid_reply`.
Chưa đủ chẩn đoán để quy lỗi cho khóa, chưa gọi TTS/STT và không tự thử lại.
Không coi khởi động live thành công là bằng chứng OpenAI dùng được. Chưa biết
chi phí thực tế trên hóa đơn; hạn mức là số yêu cầu, không phải giới hạn tiền.

**Đợt tiếp nối voice/tương thích OpenAI:** 77/77 backend tests đạt (21,64 giây),
18/18 Playwright workflows đạt (1,3 phút), TypeScript/Vite build đạt. Bổ sung
kiểm thử giữ lời nói khi server chờ, ngừng/bỏ bộ đệm/hủy đúng lượt, đầy bộ đệm
thông báo rồi gửi tiếp, ngắt giọng hỗ trợ vẫn tạm dừng; cấu hình bảo toàn thiết
lập cũ và khóa, không trả bí mật trong status, từ chối nhập khóa khi terminal
không ẩn ký tự. API có channel voice và thời gian từng bước. Lượt browser trước
có một lỗi do sửa hook trong khi Vite đang chạy kiểm thử; đã chạy lại toàn bộ
sau khi ổn định mã, đạt 18/18. Không dùng lần chạy bị ảnh hưởng để kết luận.
Trạng thái cấu hình máy: demo, chưa có API key; chưa xác minh provider hoặc
micro/loa thật. Một cảnh báo Starlette/httpx testclient vẫn còn.

**Đợt hội thoại rảnh tay:** backend đạt 73 kiểm thử, 14/14 browser workflows
đạt trong 48,5 giây; TypeScript/Vite build đạt. Bổ sung `/voice/turn`
nhận dạng → chat → đọc phản hồi tự động, bỏ bản chép im lặng, hủy đúng lượt/
chủ sở hữu và giữ phản hồi chữ khi TTS lỗi. Browser có thêm kiểm thử energy
gate, hai lượt tự động sau một lần bật, người dùng nói chen ngắt giọng Mầm,
nhánh hỗ trợ dừng micro và rời trang không gửi im lặng. Tất cả dùng micro,
provider và audio giả lập; chưa đo trên thiết bị/dịch vụ thật.

**Cập nhật đợt tác nhân Mầm/giọng nói:** 69 backend tests và 10 luồng trình
duyệt đạt. Frontend build đạt. Sáu test backend bổ sung gồm voice consent,
audio không lưu/giới hạn, nguy cơ transcript, TTS chỉ đọc server/redaction,
thu hồi giữa request/lỗi provider và quota tách người dùng chung IP. Ba luồng
browser mới kiểm tra nhân vật/khôi phục/an toàn, responsive/thiếu cấu hình,
ghi âm giả lập → sửa chữ → gửi chat → phát/dừng audio → thu hồi. Chưa dùng
micro hoặc provider thật. Chi tiết [tác nhân và giọng nói](TAC_NHAN_VA_GIONG_NOI.md).
Các số 63/7 bên dưới là mốc kiểm chứng lõi trước đợt này.

Windows, Python 3.12.10, Node 24, Chrome headless. Chỉ dữ liệu giả lập.

## Kết quả

- **63/63 backend tests pass** tại đợt `final-suite-20261022`, với pytest cache
  tắt để tránh thư mục cache cũ bị khóa. Có một cảnh báo deprecation từ
  Starlette/httpx testclient, không phải kiểm chứng provider mới.
- **7/7 luồng Playwright pass**: tài khoản bền vững/khôi phục chat/thu hồi/xóa;
  làm rõ ý mơ hồ và high không mất sau reset; chuyên gia đọc đúng tóm tắt, xác
  nhận và bị thu hồi; mood/bài tập/phản hồi/xuất/xóa; PHQ-9 mục 9 tổng thấp;
  bố cục 390px/chat/nhánh hỗ trợ; khôi phục ngữ cảnh đến muộn không ghi đè bài
  tập người dùng vừa chỉnh sửa. Lượt cuối đạt 7/7 trong 16,4 giây.
- **TypeScript + Vite build pass**. Build chạy lại trước bàn giao.
- **Docker Compose production overlay config hợp lệ**; không có Docker daemon
  nên chưa build image/chạy container. Không tự mở Docker Desktop hoặc công bố mạng.

Lệnh tương ứng, tại backend và frontend:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=./test-results/new-verification
```

```powershell
npm run build
npm run test:e2e
```

## Phạm vi kiểm thử phần mềm

63 backend tests bao gồm 35 test nền và test mới cho:

- Migration database cũ không đổi ciphertext, khởi động lặp không phá schema.
- Nâng cấp phiên khách, đăng xuất/đăng nhập/restart giữ dữ liệu, chống đọc chéo,
  auth hết hạn không xóa tài khoản, phiên khách cũ không ghi sau logout.
- Thu hồi/xóa dữ liệu dẫn xuất, từ chối ghi in-flight và từ chối lời gọi HTTP
  provider kế tiếp sau thu hồi external_ai.
- Mood/bảng hỏi/bài tập/chat cùng nhánh an toàn, GET khôi phục thể hiện nguy cơ
  từ kênh khác; reset và đổi quyền không xóa nhầm nhánh hỗ trợ RAM.
- Tín hiệu mới trong lúc sinh giữ lại phản hồi thường; sự kiện song song không
  hạ high hoặc làm mất event; lỗi dịch vụ khác nguy cơ cao.
- Chia sẻ tóm tắt theo quyền, chỉ expert được tiếp nhận, chuyển trạng thái đúng,
  thu hồi làm mất quyền xem; thiếu dịch vụ không giả đã chuyển ca.
- Version bảng hỏi, nhắc theo quyền, EviOCEAN job nhiều conversation tự chạy
  khi đồng ý nhưng không bịa trait/evidence; tắt xóa profile/job.
- CARE unknown/tám trường; truy hồi loại draft/withdrawn/mẫu production, kho
  trống không tự seed; pipeline offline/online dùng cùng encoder và ba điểm,
  từ chối vector NaN/sai cấu trúc.
- Backup/restore không ghi đè đích, giữ dữ liệu mã hóa; retention xóa nguồn và
  trạng thái dẫn xuất; production từ chối thiếu key/cookie secure.
- Giữ kiểm thử nền về AI lỗi/JSON lỗi/đầu ra bị giữ lại, che email/điện thoại,
  cookie/Origin/body/rate limit, chấm điểm xác định và xuất đầy đủ.

## Kiểm thử AI giả lập và đánh giá mô hình thật

Suite giả lập HTTP/JSON và encoder/projector có kiểm soát. Nó chứng minh hợp
đồng phần mềm, không chứng minh chất lượng model, embedding hay hiệu quả hỗ trợ.
Không có lượt gọi model thật, giá provider hoặc đo lường lâm sàng trong đợt này.

Đánh giá thật phải có tập tình huống Việt tách biệt, được phép sử dụng, rubric
chuyên gia, nhãn nguy cơ độc lập; đo bỏ sót/cảnh báo sai, phủ định/trích dẫn,
đầu ra nguy hiểm, lỗi provider, độ trễ/token/chi phí. Với CogRAG, so sánh semantic
baseline với fusion ba biểu diễn cùng encoder và tập nguồn cố định; kiểm tra
trace nguồn và trường hợp không có nguồn phù hợp. Với CARE/EviOCEAN, cần mã,
checkpoint/nhãn và đánh giá ổn định/không kết luận. Không cộng các test phần
mềm thành tỷ lệ chính xác AI hoặc tuyên bố tái lập bài báo.

## Giới hạn rà soát

Đã rà soát inline và sửa các lỗi được tái hiện bằng test: quota tính GET như AI,
phiên khách cũ ghi sau logout, provider gọi tiếp sau revoke, reset/đổi quyền mất
an toàn, trạng thái dẫn xuất giữ nguồn hết hạn, và phản hồi thường vượt tín hiệu
mới. Một lượt reviewer độc lập phát hiện vấn đề revoke provider; lượt review
không hoàn tất do giới hạn sử dụng của agent. Đây chưa phải kiểm toán độc lập
đầy đủ. Cần kiểm thử tải/đa tiến trình, pentest, chuyên gia và diễn tập vận hành
trước khi dùng dữ liệu thật.
