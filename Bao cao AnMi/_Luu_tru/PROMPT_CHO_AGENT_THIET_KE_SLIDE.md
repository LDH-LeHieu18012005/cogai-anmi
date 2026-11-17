# Prompt giao cho agent thiết kế slide AnMi

Bạn là chuyên gia thiết kế pitch deck khởi nghiệp, có khả năng xây dựng câu chuyện kinh doanh, kiểm tra logic tài chính và xuất PowerPoint chỉnh sửa được. Hãy đọc bộ tài liệu tôi đính kèm và THỰC HIỆN thiết kế một bộ slide hoàn chỉnh, không dừng ở dàn ý hoặc tư vấn.

## 1. Nhiệm vụ và bối cảnh

Dự án dự thi khởi nghiệp: **CogAI — Hệ sinh thái AI sàng lọc sớm và hỗ trợ sức khỏe tinh thần**. Trợ lý giao tiếp mang tên **AnMi**: “An” gợi sự bình an, “Mi” tạo cảm giác gần gũi. AnMi thuộc CogAI; không đổi tên toàn bộ hệ sinh thái thành tên phần cứng.

Đối tượng ban giám khảo quan tâm: vấn đề thực tiễn, bằng chứng nhu cầu, khác biệt, sản phẩm, khách hàng trả tiền, khả năng vận hành và kiếm tiền. Tôi muốn phần sản phẩm và kinh doanh là trọng tâm; phần nghiên cứu củng cố niềm tin, không biến bài pitch thành báo cáo thuật toán.

Yêu cầu bắt buộc: **đúng 10 slide, tiếng Việt, tỷ lệ 16:9, trình bày trong 5 phút**. Tổng thời gian phân bổ trong speaker notes phải bằng **300 giây**. Không thêm slide cảm ơn hoặc phụ lục vào tệp trình chiếu chính; nguồn và phân tích dài có thể xuất thành tài liệu riêng.

## 2. Đọc và đối chiếu tài liệu

Đọc `00_DOC_TRUOC.md` và hồ sơ thuyết minh, sau đó đọc mô hình tài chính, bản giải thích nguồn, các bài báo, hình pipeline và bản slide hiện tại. Bản slide hiện tại chỉ là nền nội dung để thiết kế lại; bạn được thay bố cục, cách kể chuyện, tiêu đề và đồ họa.

Thứ tự xử lý khi thông tin khác nhau:

1. Chỉ dẫn trực tiếp trong prompt này và thông tin người dùng xác nhận, đặc biệt hai ảnh thiết bị “quỷ nhỏ”.
2. Bảng Excel và tài liệu giải thích hiện hành cho dự báo đã tính lại; hồ sơ gốc để đối chiếu và trích xuất thông tin.
3. Bài báo gốc cho kết quả nghiên cứu, kèm bộ dữ liệu/phép đo và giới hạn.
4. Bản slide cũ để tham khảo nội dung và phong cách; không mặc nhiên xem mọi con số là kết quả thực tế.

Không tự thay số liệu chỉ để câu chuyện hấp dẫn hơn. Nếu cần sửa một giả định, nêu lý do và cập nhật đồng bộ doanh thu, chi phí, lợi nhuận, dòng tiền và speaker notes.

## 3. Nhận diện đúng thiết bị — rất quan trọng

Thiết bị tôi đang dùng là mẫu **“Quỷ nhỏ thông thái / Monter Desk AI”** trong HAI ẢNH tôi gửi cùng bộ tài liệu: thân trắng có sừng, khung mặt tím, màn hình chữ nhật. Tên “Monter Desk AI” là chữ trên ảnh, không tự sửa thành tên hãng hay mã sản phẩm đã xác minh.

- Dùng hai ảnh này để nhận diện và trình bày phần cứng. Có thể cắt khung ảnh để bố cục đẹp, giữ đúng hình dáng; không tạo ảnh robot khác rồi gọi đó là ảnh nguyên mẫu thực.
- Thiết bị màn hình tròn EchoEar/MYHealth xuất hiện trong hồ sơ là tài liệu lịch sử của nguyên mẫu khác. Không dùng nó làm ảnh mẫu quỷ nhỏ và không chuyển thông số, giá hay kiểm thử của nó sang mẫu mới.
- Chưa xác minh chip, RAM/Flash, kích thước/độ phân giải màn hình, số micro, công suất loa, nguồn/pin, phụ kiện, giá mua và khả năng nạp firmware/API của mẫu quỷ nhỏ. Không suy ra các thông số đó từ ảnh.
- **2 triệu đồng/bộ là hạn mức kế hoạch**, suy từ 20 triệu/10 thiết bị trong thuyết minh; chưa phải giá mua, báo giá hay giá thành thị trường.
- Có thể mô tả kiến trúc dự kiến: phần cứng làm kênh tương tác, kết nối lõi AI trên máy chủ. Chỉ nói đã tích hợp/chạy được khi có bằng chứng riêng trên đúng mẫu này.
- Nếu môi trường của bạn không đọc được ảnh đính kèm, dùng minh họa có nhãn rõ và liệt kê ảnh còn cần đặt; không thay bằng mẫu robot sai.

## 4. Câu chuyện và cấu trúc 10 slide

Dùng cấu trúc dưới đây làm khung; được điều chỉnh nhịp kể trong từng slide nhưng phải bao phủ đủ mọi nội dung:

| Slide | Thời gian | Nội dung và thông điệp cần có | Hướng thể hiện |
|---|---:|---|---|
| 1 | 25 giây | Câu chuyện sinh viên xa nhà, áp lực khó chia sẻ → giới thiệu AnMi và giá trị cốt lõi | Một tình huống ngắn, tên AnMi nổi bật. Ghi rõ tình huống minh họa nếu không có nguồn xác minh |
| 2 | 30 giây | Nhu cầu và thị trường: sinh viên/công nhân, người dùng khác người mua, nhóm khởi đầu và vùng mở rộng | 2–3 số liệu có nguồn, một cách tính mục tiêu tiếp cận từ số tổ chức/suất. Phân biệt quy mô, nhu cầu và khả năng trả phí |
| 3 | 40 giây | Pipeline của hệ sinh thái và các thành phần kết nối với nhau | Sơ đồ vẽ lại, dễ đọc; phân biệt phần đã có, đang tích hợp và theo kế hoạch |
| 4 | 25 giây | Hành trình sản phẩm + năng lực nghiên cứu/nguyên mẫu | Ảnh giao diện hoặc ba bước sử dụng; 1–2 kết quả nghiên cứu/kiểm thử có ý nghĩa và đúng giới hạn |
| 5 | 30 giây | Mô hình kinh doanh, ai trả tiền, trả cho giá trị gì, giá dự kiến và cạnh tranh | Sơ đồ B2B2C, giá gói, giá trị cho tổ chức; tham chiếu đối thủ công bằng, không so sánh dịch vụ khác phạm vi như tương đương |
| 6 | 25 giây | Chiến lược marketing, bán hàng, kích hoạt và giữ chân | Hai phía: người mua và người dùng; phễu mục tiêu 10 → 6 → 2 → 1, kênh và ngân sách rõ |
| 7 | 25 giây | Thiết bị quỷ nhỏ, vai trò phần cứng, linh kiện và hạn mức mua sắm | Ảnh đúng mẫu + chức năng các nhóm phần cứng; chi tiết BOM trong tài liệu kèm. Không bịa đơn giá linh kiện chưa có |
| 8 | 30 giây | Chi phí cố định, biến đổi, ngân sách năm đầu và cách tối ưu | Bảng chi phí gọn, phép tính lãi đóng góp; phân biệt đầu tư ban đầu với vận hành, không cộng trùng |
| 9 | 40 giây | Kế hoạch tài chính, lợi nhuận, hòa vốn, hoàn vốn và nhu cầu vốn | Biểu đồ/bảng tài chính dễ đọc; nêu kịch bản cơ sở và ít nhất một rủi ro bất lợi |
| 10 | 30 giây | Kế hoạch triển khai, năng lực nhóm, đề nghị đồng hành và mốc tiếp theo | Timeline với đầu ra/điều kiện; lời kêu gọi cụ thể, thông tin liên hệ nếu có trong hồ sơ |

Không cố nhét toàn bộ báo cáo vào mặt slide. Chỉ trình bày thông điệp và số cần nói trong 5 phút; giải thích, nguồn đầy đủ, công thức và lưu ý đặt trong notes/tài liệu kèm.

## 5. Pipeline cần thể hiện đúng

Vẽ rõ mối quan hệ giữa:

- Người dùng → web, thiết bị để bàn, ứng dụng/đồng hồ theo lộ trình.
- Cổng API chung, tài khoản và đồng ý dữ liệu; luồng giọng nói có STT/TTS nếu mô tả.
- Kiểm tra nguy cơ và nhánh ưu tiên tìm người thật khi cần; hiển thị liên hệ khác với xác nhận tiếp nhận ca.
- Lõi AnMi: hiểu cảm xúc/appraisal → CogRAG truy hồi theo ngữ nghĩa, nhận thức và CBT → sinh phản hồi → kiểm tra đầu ra.
- Bộ nhớ theo quyền, kho tri thức có nguồn; EviOCEAN/cá nhân hóa chạy khi có nhu cầu và đủ bằng chứng.
- Phản hồi trả về đúng kênh; báo cáo tổng hợp cho tổ chức có quyền riêng, không mở hội thoại cá nhân.

Sơ đồ kiến trúc đích không có nghĩa bốn kênh đã kết nối và hoạt động hoàn chỉnh. Không cho phép nhánh cá nhân hóa bỏ qua kiểm tra nguy cơ.

## 6. Số liệu và tài chính phải nhất quán

Các số sau là **giả định mô hình**, không phải kết quả kinh doanh đã đạt:

- Gói tổ chức dự kiến 12.000–15.000đ/suất/tháng; giá bình quân cơ sở 14.000đ. Suất được cấp quyền tính phí khác người hoạt động.
- Biến phí cơ sở 5.000đ/suất/tháng; lãi đóng góp 9.000đ, biên 64,3%, trước chi cố định và thuế. Phải đo lại toàn bộ tải, kể cả tải người dùng miễn phí.
- Tổng ngân sách năm đầu 260 triệu: 78 hạ tầng/AI + 78 dữ liệu/chuyên môn + 20 pháp lý + 30 thiết bị + 28 thí điểm/khảo sát/truyền thông + 26 dự phòng. Nhóm sáng lập chưa tính lương năm đầu theo hồ sơ.
- Trong 30 triệu thiết bị: 20 triệu cho 10 bộ thí điểm + 10 triệu cho thiết bị kiểm thử. Không cộng giá từng linh kiện đã nằm trong bộ mua đầy đủ.
- Cố định năm 2 là 570 triệu, năm 3 là 720 triệu; có bảng phân rã trong Excel. Chưa phải báo giá lương toàn phần cho đủ 5 sáng lập hoặc chi phí chuyên gia trực 24/7.
- Suất trả phí bình quân năm 1–5: 0 / 3.000 / 8.000 / 15.000 / 25.000.
- Doanh thu triệu đồng: 0 / 504 / 1.344 / 2.520 / 4.200.
- Lãi sau thuế giả định triệu đồng: −260 / −246 / 115,2 / 416 / 800.
- Thuế mô hình 20% phần lãi dương, chưa bù lỗ; không coi đây là kết luận thuế thực tế.
- Hòa vốn vận hành năm 3 khoảng 6.667 suất; hoàn vốn dòng tiền giản lược khoảng 3,94 năm từ 10/2026.
- Thâm hụt lũy kế tối đa 506 triệu; ngoài 260 triệu năm đầu cần ít nhất 246 triệu bổ sung, chưa đệm vốn. Vốn góp/tài trợ/gọi vốn không phải doanh thu.
- Kịch bản số suất thấp hơn 30% chưa hoàn vốn sau 5 năm. Giá 12.000đ hoặc biến phí 8.000đ có bảng độ nhạy riêng.

Dòng tiền hiện còn giản lược, chưa đầy đủ vốn lưu động, khấu hao, đầu tư bổ sung và chi phí vốn. Nếu thiết kế trình bày NPV/IRR, phải tính lại từ dòng tiền có mốc thời gian và giải thích giả định; không lấy số cũ trong hồ sơ khi mô hình đã khác.

## 7. Bằng chứng và cách sử dụng nguồn

- Chỉ đưa khảo sát đã thu thật hoặc nghiên cứu công bố lên slide như bằng chứng. Các sheet khảo sát trống là kế hoạch thu thập; dữ liệu mô phỏng, nếu có ở nơi khác, không phải khảo sát thị trường.
- Không tạo người trả lời, cỡ mẫu, ngày khảo sát, khách hàng, hợp đồng, doanh thu, đối tác hoặc lời chứng thực rồi trình bày như có thật. Ẩn danh không thay đổi yêu cầu nguồn gốc dữ liệu.
- Mẫu 1.788 sinh viên và 1.200 công nhân là các nghiên cứu lịch sử/quần thể cụ thể; không suy rộng thành tỷ lệ toàn Việt Nam năm 2026.
- 84/84 kiểm thử MYHealth dùng AI giả lập; không phải độ chính xác phát hiện nguy cơ, thử nghiệm lâm sàng hoặc kiểm thử đã thực hiện trên mẫu quỷ nhỏ.
- Kết quả bài báo dùng dữ liệu tiếng Anh; không chứng minh hiệu quả lâm sàng tiếng Việt. Trạng thái chấp nhận công bố theo hồ sơ cần được quy nguồn, không tự xác nhận nếu chưa kiểm tra.
- Câu chuyện mở đầu dùng tình huống minh họa nếu chưa có nguồn về trường hợp thật. Không mô tả tự sát bằng hình ảnh/phương thức gây sốc hoặc quy cho một nguyên nhân đơn lẻ.
- AnMi là công cụ sàng lọc/hỗ trợ/tự chăm sóc; không chẩn đoán, không kê đơn, không hứa thay thế chuyên gia.
- Nếu tìm thêm số liệu/giá thị trường, dùng nguồn gốc, ghi kỳ dữ liệu, phạm vi, đường dẫn và ngày kiểm tra. Giá niêm yết khác giá mua/báo giá hợp đồng.

## 8. Định hướng thiết kế

Phong cách startup công nghệ hỗ trợ sức khỏe tinh thần: rõ ràng, ấm áp, đáng tin, có bản sắc. Tham khảo nền ngà, xanh trầm, bạc hà và tím nhẹ liên hệ với thiết bị. Bạn được cải thiện bảng màu và bố cục để tạo bộ deck chuyên nghiệp hơn.

- Mỗi slide một thông điệp chính; dùng tiêu đề kết luận và khoảng trắng tốt.
- Ưu tiên ảnh sản phẩm thật, giao diện, pipeline, biểu đồ và con số nổi bật. Đồ họa phục vụ giải thích cách hoạt động, giá trị và dòng tiền.
- Hạn chế đoạn văn; nội dung chính thường 24–32pt, tiêu đề 32–44pt trên PowerPoint. Không ép chữ nhỏ để nhét nội dung.
- Bảng số liệu cần có đơn vị, nhãn, tương phản tốt; không lạm dụng trang trí, icon chung chung hoặc chuyển cảnh phức tạp.
- Giữ phần lớn chữ, bảng, pipeline và biểu đồ sửa được trong PowerPoint. Không xuất mỗi slide thành một ảnh toàn trang.
- Có thể dùng bố cục hiện tại làm tham khảo, nhưng hãy thiết kế lại thực sự nếu giúp bài pitch tốt hơn.

## 9. Đầu ra phải giao

1. `AnMi_Pitch_Final.pptx`: đúng 10 slide, thành phần chính chỉnh sửa được.
2. `AnMi_Pitch_Final.pdf`: khớp PowerPoint, đúng 10 trang, không bị cắt/tràn.
3. Speaker notes tiếng Việt cho từng slide: thời gian, lời nói tự nhiên, nguồn và giới hạn; tổng phân bổ 300 giây.
4. Một trang tổng quan 10 slide để xem nhanh.
5. Danh mục nguồn và bảng các giả định/chỗ còn chờ xác nhận; nếu sửa mô hình tài chính, giao Excel có công thức đã cập nhật.

Trước bàn giao, render và xem toàn bộ slide; kiểm tra dấu tiếng Việt, căn chỉnh, cỡ chữ, hình sai mẫu, tràn nội dung, phép tính, đơn vị, nguồn và tổng thời gian. Nếu công cụ không xuất được PPTX chỉnh sửa được, nói rõ giới hạn và giao định dạng biên tập tốt nhất có thể; không gọi một tệp ảnh hoặc PDF là PowerPoint chỉnh sửa được.

Hãy tự quyết các lựa chọn thiết kế thông thường. Với giá/cấu hình còn thiếu, ghi rõ “chưa xác nhận” hoặc “hạn mức kế hoạch” và hoàn thành các phần độc lập; không dừng toàn bộ công việc để hỏi lại những thông tin đã có trong bộ tài liệu.
