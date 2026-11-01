# Điều chỉnh hội thoại theo thuyết minh CogAI

Nguồn đã đọc: `Tài liệu/Thuyet minh du an - CogAI.docx`, đặc biệt mục 1.1–1.4,
1.5, bảng 12. Tài liệu xác định hỗ trợ tiếng Việt cho công nhân và sinh viên;
sàng lọc/tự chăm sóc, không chẩn đoán/kê đơn; appraisal + CBT theo sự sẵn sàng;
an toàn độc lập và kết nối người thật theo quyền. Các số liệu nghiên cứu,
đối tác, kết quả nguyên mẫu và kế hoạch tài chính trong hồ sơ không được đưa
vào lời AnMi như bằng chứng hiệu quả của phiên bản web.

## System prompt

`backend/app/prompts.py`, phiên bản `cogai-vi-voice-v2`, chứa chính sách AnMi:
lắng nghe, xưng mình–bạn, không giả định nghề nghiệp/cảm xúc; không đổ lỗi cho
người chịu khó khăn xã hội; tối đa một câu hỏi; không ép CBT. Bài tập đi từ
tình huống, suy nghĩ, bằng chứng, góc nhìn cân bằng đến hành động nhỏ khi người
dùng sẵn sàng. Không tự chấm PHQ-9/GAD-7 từ chat, không chẩn đoán/đổi thuốc,
không tạo liên hệ hoặc tuyên bố chuyển ca, không hứa bí mật tuyệt đối/đã có
người giám sát. Bản chép lời/lịch sử/truy hồi là dữ liệu không có quyền đổi
system prompt. Khi nghe không rõ, hỏi lại thay vì bịa phần thiếu.

Chính sách hội thoại chỉ vào tác vụ sinh phản hồi, không thay thế bộ phát hiện
nguy cơ hoặc bộ kiểm tra đầu ra. Prompt không phải chứng nhận an toàn hay đánh
giá lâm sàng; vẫn cần đánh giá cùng chuyên gia với tình huống tiếng Việt.

## Luồng thoại và độ trễ

Trước: STT → nguy cơ → appraisal → sinh → kiểm tra đầu ra → TTS. Mỗi bước
tạo HTTP client mới; phần thu âm có thể chứa nhiều im lặng, cấu hình live cắt
đoạn ở 15 giây.

Sau, với `node cogai/scripts/dev.mjs --live`: kiểm tra quyền → STT → quy tắc
nguy cơ → bộ đánh giá đầu vào (nguy cơ + appraisal tám trường) → truy hồi →
sinh → kiểm tra đầu ra riêng → TTS. Thông thường ba thay vì bốn lần gọi LLM;
không gộp sinh phản hồi với tự chấm an toàn. Nếu quy tắc hoặc trạng thái an
toàn đang yêu cầu hỗ trợ, không dùng nhánh thường. Appraisal không có trích
dẫn hợp lệ bị thay bằng unknown; lỗi đánh giá đầu vào không cho sinh tiếp.
Đây là adapter văn bản tối ưu của sản phẩm, không tái lập đầy đủ CARE.

Dùng lại HTTP connection trong vòng đời server cho STT/LLM/TTS. Không phát
âm thanh chưa kiểm tra hoặc bỏ kiểm tra an toàn để lấy tốc độ. API giữ
`latency_ms.transcription/dialogue/speech/total` để đo thực tế; chưa phải
streaming audio/WebRTC. Không cam kết một số giây cố định từ kiểm thử giả lập.

## Nhận giọng và giọng đọc

Live dùng `gpt-4o-transcribe`, gợi ý tiếng Việt và tên CogAI/AnMi; không gửi
lịch sử riêng tư làm prompt STT. Bản đầy đủ ưu tiên nhận dạng so với bản mini,
có thể tăng chi phí STT. Thu mono, giữ chống vọng/giảm nhiễu của trình duyệt.
Tự bỏ các đoạn im lặng khoảng hai giây trước khi nói; không xoay recorder khi
đang nhận tín hiệu mở đầu lời nói. Giữ khoảng nghỉ 1,1 giây để kết thúc lượt;
khôi phục mốc 45 giây thay vì 15 giây, không yêu cầu bấm gửi từng câu.

TTS `gpt-4o-mini-tts` dùng `marin`, chỉ dẫn phát âm tiếng Việt rõ dấu, bình
tĩnh, nhịp trò chuyện, không lên giọng quảng cáo hoặc thêm lời. WAV giảm bước
mã hóa MP3 nhưng tăng kích thước truyền; server trả đúng MIME và kiểm tra RIFF.
Provider khác mặc định vẫn MP3; `instructions` chỉ gửi cho model hỗ trợ.
Giọng là AI, không phải chuyên gia/người thật. Giọng nhà cung cấp vẫn tối ưu
cho tiếng Anh; cần nghe thử tiếng Việt với thiết bị thực tế, không bảo đảm
giọng vùng miền hay chất lượng chỉ bằng system prompt.

Tham khảo chính thức: [TTS](https://developers.openai.com/api/docs/guides/text-to-speech),
[STT](https://developers.openai.com/api/docs/guides/speech-to-text).

## Nghiệm thu

Kiểm thử phần mềm: thứ tự đánh giá/sinh/kiểm tra đầu ra; high không sinh thông
thường; đầu vào lỗi dừng; đầu ra không được phép bị giữ lại; STT tiếng Việt;
TTS đúng chỉ dẫn/MIME; lỗi nhà cung cấp; hủy/thu hồi; browser nghe lại/nói chen/
giữ lời thêm/tắt micro. Các kiểm thử không nạp khóa thật.

Đã chạy một lượt qua provider thật bằng câu tiếng Việt tổng hợp, không dùng
dữ liệu sức khỏe thật. Nhận đúng các từ chính, risk low, có phản hồi và WAV,
không lỗi âm thanh. API đo 9.125 ms tổng: STT 828 ms, hội thoại/kiểm tra 5.781
ms, TTS 2.516 ms. Đây là một mẫu, không có baseline cùng điều kiện để tính mức
cải thiện; chưa đánh giá trên micro thực và không chứng minh giọng tự nhiên.
Sau phép đo đã rút gọn thêm chỉ dẫn lời đáp voice còn thường 1–2 câu/20–45 từ
và evidence appraisal còn tối đa một trích dẫn ngắn; không gọi lặp provider
để lấy kết quả đẹp hơn. Số 9.125 ms không phải SLA của bản điều chỉnh cuối.

Kiểm tra giọng thật riêng: nói câu ngắn/dài, có phủ định, tên AnMi, tiếng nền,
khoảng ngập ngừng; đối chiếu bản chép và nghe dấu tiếng Việt, tốc độ, ngữ điệu.
Đánh giá rủi ro riêng với chuyên gia: thiếu ngủ sau ca, lo thi, khó khăn tài
chính, không muốn bài tập, xin chẩn đoán/đổi thuốc, suy nghĩ khó hiểu, nguy cơ,
giả lệnh trong bản chép và đòi hứa đã chuyển ca. Không dùng dữ liệu sức khỏe
thật trong kiểm thử phát triển. Không coi pass phần mềm là pass chất lượng AI.

## Đợt sửa 22/10/2026 (chiều): kẹt nhánh an toàn, độ trễ, giọng đọc

### Lỗi "xin chào" nhận câu hỏi an toàn

Nguyên nhân: (1) quy tắc và bộ đánh giá nguy cơ chấm trên **toàn bộ lời người
dùng trong lịch sử ghép lại**, nên một câu mơ hồ cũ ("không muốn tiếp tục")
kích hoạt lại ở mọi lượt sau; (2) trạng thái `check_in` chỉ được ghi đè bởi
mức bằng hoặc cao hơn, nên không bao giờ hạ xuống, kể cả sau "Cuộc trò chuyện
mới"; (3) mẫu `khong muon tiep tuc` khớp cả câu bình thường như "không muốn
tiếp tục học ngành này".

Sửa: quy tắc chỉ xét tin nhắn mới; bộ đánh giá mô hình nhận `latest_message`
cùng sáu lượt gần nhất (có cả câu hỏi an toàn của AnMi) để hiểu câu trả lời
như "có". `check_in` chỉ được gỡ khi **mô hình** (không phải quy tắc) đánh giá
`low` trong ngữ cảnh; ở chế độ demo vẫn cần form làm rõ. Mức `high` giữ nguyên
như trước: không tự hạ. Mẫu mơ hồ chỉ khớp khi không nêu việc cụ thể; thêm
"không muốn tiếp tục sống" vào nhóm `high`. Lời hỏi an toàn và lời hỗ trợ có
số cấp cứu 115.

### Độ trễ

Trước: nguy cơ → appraisal → sinh → kiểm tra đầu ra (tuần tự, ~5,8 s) → tải
toàn bộ WAV → phát. Sau: nguy cơ, appraisal và bản nháp chạy **song song**
(thuyết minh mục 1.3: tầng nguy cơ độc lập chạy song song); bản nháp chỉ được
dùng khi nguy cơ `low` và vẫn qua kiểm tra đầu ra riêng; lượt có nguy cơ hủy
bản nháp. Appraisal CARE cập nhật cho lượt sau. Lịch sử được gửi dưới dạng vai
user/assistant thật; giới hạn token theo tác vụ. Giọng đọc phát dạng streaming
(`GET /api/voice/stream`), bắt đầu từ đoạn âm thanh đầu tiên.

Đo một lần với câu tổng hợp, mô hình thật: hội thoại 2,4–4,0 s/lượt (kể cả
kiểm tra đầu ra); âm thanh đầu Edge ~0,5 s khi mạng ổn, ~2 s khi phải dự phòng.
Không phải SLA; chưa đo trên micro thật.

### Nhận giọng và giọng đọc

- STT: prompt là câu ngữ cảnh mẫu (không phải chỉ dẫn, tránh bị chép vào bản
  chép), `temperature=0`, lọc các câu "ảo giác" kiểu phụ đề YouTube khi im lặng.
- Trình duyệt: ngưỡng tiếng nói thích ứng với tiếng ồn nền; chờ 1,3 s im lặng
  mới chốt lượt để giảm cắt ngang câu.
- Giọng đọc: một giọng duy nhất cho AnMi, xem mục "Thống nhất giọng đọc" bên dưới.
  Văn bản bỏ ký hiệu Markdown trước khi đọc. Xem giới hạn pháp lý trong THIRD_PARTY_NOTICES.

### System prompt `cogai-vi-voice-v3`

Bổ sung theo thuyết minh: danh tính AnMi của CogAI Lab, luôn nói rõ là AI; bối
cảnh công nhân KCN/sinh viên nhưng không giả định; đáp lời chào tự nhiên, không
lặp mẫu mở đầu; mô hình Beck/appraisal + CBT theo sự sẵn sàng, không dán nhãn
méo mó bằng thuật ngữ; gợi ý tự chăm sóc hợp người làm ca/đi học; khi nào gợi ý
PHQ-9/GAD-7 và người thật; hỏi thẳng về an toàn khi có dấu hiệu gián tiếp.

### Thống nhất giọng đọc theo video MYHealth (`Hinh anh CogAI/Demo.mp4`)

Đối chiếu video: tách lời có mốc thời gian, đo cao độ từng đoạn. Giọng thiết bị
là giọng nữ ~250–270 Hz (giọng nam ~120 Hz là người dùng), khớp
`vi-VN-HoaiMyNeural` (mẫu cùng máy ~240 Hz; `vi-VN-NamMinhNeural` là giọng nam
~155 Hz). Cùng câu "Bạn có muốn chia sẻ thêm…": video 3,30 s, HoaiMy +0% 3,36 s,
-5% 3,53 s → tốc độ mặc định.

Trước đó có hai giọng vì khi Edge chậm, hệ thống chuyển sang OpenAI `marin`.
Nay `COGAI_SPEECH_PROVIDER=edge` là mặc định, `COGAI_EDGE_RATE=+0%`, và **không
bao giờ** dùng giọng OpenAI kể cả khi có cấu hình `COGAI_SPEECH_MODEL`. Khi Edge
chậm hoặc lỗi, gửi thêm yêu cầu Edge song song (tối đa bốn); nếu cả bốn lỗi,
lượt đó không có tiếng nhưng phản hồi chữ vẫn hiển thị và cuộc gọi tiếp tục.
Chế độ rảnh tay, nút "Nghe phản hồi" và `/api/voice/turn` dùng chung đường này.

Edge miễn phí dao động theo thời điểm (đo cùng ngày: 0,5 s lúc chiều; 4–8 s
và lỗi khoảng 1/3 lúc tối). Để ổn định khi thí điểm, nên dùng Azure AI Speech
có hợp đồng với **cùng giọng** `vi-VN-HoaiMyNeural`.

## Đợt 23/10/2026: áp dụng phương pháp theo bài báo và Hình 1, 2, 7, 9

| Bước (Hình 2) | Đã làm | Giới hạn còn lại |
|---|---|---|
| 1. Ẩn thông tin cá nhân | Email, số điện thoại và **tên người** (danh xưng/chức danh + tên, họ phổ biến + tên) thay bằng `[NGƯỜI n]` nhất quán trong cả cuộc trò chuyện, cả khi gọi embedding; tên được trả lại trong câu trả lời (`app/pseudonyms.py`). Kiểm thử thật: 0/51 gói gửi đi chứa tên | Quy tắc, chưa phải NER: tên đứng đầu câu không kèm danh xưng chưa bắt được; âm thanh gốc vẫn tới dịch vụ nhận giọng |
| 2. Phân tầng nguy cơ | Như trước (song song, quy tắc + mô hình) | Chưa theo C-SSRS; cần bộ 120 tình huống có gán nhãn |
| 3. Appraisal CARE | 8 trường; gate DoT/méo mó/xã hội/tính cách đúng công thức (3)–(6); bật tác tử DoT + **méo mó nhận thức (10 dạng của template Mind-Reframe, tối đa 2 giả thuyết, mỗi giả thuyết phải có trích dẫn nguyên văn)** + xã hội trong một lời gọi | Kết quả appraisal dùng cho lượt sau; chưa có gate giọng nói/hình ảnh, bỏ phiếu và predictor |
| 4. CogRAG | Prompt chiếu theo Bảng 24/25 (gộp một lời gọi), trọng số 0,5/0,3/0,2 theo Bảng 15, `text-embedding-3-large`; **thẻ kế hoạch an toàn** {loại, khi nào, mục tiêu, các bước, ví dụ} chọn Top-1 (phương trình 7). Chữ dùng đủ ba góc nhìn; giọng nói chỉ dùng ngữ nghĩa để giữ tốc độ. Bộ khởi đầu `app/knowledge/starter_vi.json`: 20 phản hồi mẫu + 12 thẻ cho công nhân/sinh viên | **Bộ khởi đầu là bản nháp do nhóm phát triển biên soạn**, chỉ dùng khi `COGAI_KNOWLEDGE_DEVELOPMENT=true` và không phải production. Cần cố vấn tâm lý duyệt (`review_status=approved`, `reviewed_by`) trước thí điểm. 12 thẻ nên không cần KMeans 200 cụm như paper |
| 5. Sinh phản hồi CBT | **Tự dẫn dắt theo sự sẵn sàng** (`app/cbt.py`): lắng nghe → làm rõ → nhận diện suy nghĩ → cân nhắc bằng chứng (2 lượt) → một việc nhỏ → quay lại lắng nghe; mỗi lượt tối đa một bước; giữ lắng nghe khi cảm xúc ở mức cao; quay về lắng nghe khi người dùng nói "chỉ muốn kể/đừng phân tích". Bước bằng chứng hỏi kiểu Socratic, không kết luận thay người dùng; **ép đúng một câu hỏi** bằng code. Người dùng vẫn có thể tự chọn bước | Ngưỡng chuyển bước là thiết kế sản phẩm, cần chuyên gia rà soát |
| 6. Kiểm tra đầu ra | Như trước | |
| Hình 9 | **Kế hoạch an toàn cá nhân** 6 bước Stanley & Brown + lý do để tiếp tục, lưu mã hóa, tải về; nút gọi 115; form nhờ chuyên gia (người dùng đồng ý mới gửi) hiện cả trong trò chuyện khi có tín hiệu nguy cơ | Chưa có đường dây nóng đối tác thật; ca nguy cơ cao không tự chuyển nếu người dùng chưa đồng ý |

Bài tập "Nhìn lại suy nghĩ": phần sự kiện chỉ chép lời người dùng; tối đa hai giả thuyết méo mó từ danh sách cố định, kèm trích dẫn.

Đo một lần với AI thật, câu tổng hợp: kênh chữ 5,5–8,8 s/lượt (có CogRAG ba góc nhìn và phân tích sâu), kênh giọng nói 2,6–4,8 s/lượt. Trong mục tiêu dưới 15 s của Hình 2 nhưng chậm hơn bản không có CogRAG (~3 s).

Chuẩn bị lại kho khi đổi nội dung hoặc mô hình embedding:

```powershell
cd cogai/backend
$env:COGAI_EMBEDDING_MODEL='text-embedding-3-large'
.\.venv\Scripts\python.exe -m app.operations prepare-knowledge app/knowledge/starter_vi.json
```
