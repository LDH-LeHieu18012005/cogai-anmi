# Triển khai lõi web CogAI — 22/10/2026

## Kết quả đợt triển khai

Đã triển khai các giai đoạn tài khoản/quyền/bộ nhớ/điều phối/an toàn, adapter
nghiên cứu, công cụ expert và công cụ vận hành. 63 backend tests và 7 browser
workflows đạt; frontend build đạt. Chi tiết phần thiếu và giới hạn ở
[biên bản bàn giao](BAN_GIAO_2026_10_22.md). Kế hoạch không được dùng để tự
đánh dấu điều kiện chuyên môn/đối tác/model thật đã hoàn tất.

Quyết định thực hiện: giữ schema legacy bằng migration additive; dùng một API
worker vì chưa có kho RAM/locks phân tán; EviOCEAN abstain thay preliminary
fallback khi thiếu bằng chứng; không tự nạp corpus; trạng thái tiếp nhận phụ
thuộc thao tác người thật. Các quyết định và chi phí giới hạn có trong bàn giao.

Yêu cầu ràng buộc: giữ React/FastAPI, dữ liệu cũ, không công bố mạng,
không dùng dữ liệu sức khỏe thật, không coi adapter/prompt là tái lập nghiên cứu.
Thực hiện trực tiếp theo ủy quyền trong yêu cầu; không có Git repository nên
không tạo commit/worktree. Mọi thử nghiệm dùng database riêng.

## Thiết kế và thứ tự

1. Migration có phiên bản giữ nguyên sessions/records mã hóa cũ. Tài khoản bí danh
   có mật khẩu băm, sở hữu kho dữ liệu độc lập với phiên đăng nhập 24 giờ.
   Phiên khách cũ vẫn dùng được. Nâng cấp thành tài khoản giữ dữ liệu của phiên.
2. Đồng ý theo mục đích: lưu, AI ngoài, cá nhân hóa, chia sẻ chuyên gia, nhắc
   sàng lọc. Thu hồi có hiệu lực trên yêu cầu đang chạy bằng revision; xóa dữ
   liệu dẫn xuất tương ứng. Kho không lưu chỉ giữ RAM đến hết phiên/restart.
3. Điều phối chung lấy lịch sử/trạng thái từ server, kiểm tra nguy cơ trước
   appraisal/truy hồi/sinh; bài tập Lumina là công cụ tùy chọn. Sự kiện an toàn
   từ mọi kênh giữ nhánh hỗ trợ khi đổi trang hoặc reset chat; lỗi dịch vụ có
   trạng thái riêng, không tự gán nguy cơ cao.
4. CARE: schema tám trường đúng bài, bằng chứng và unknown, cập nhật theo lượt,
   phân tích sâu có chọn lọc. CogRAG: hợp đồng ba biểu diễn, pipeline offline,
   fusion, nguồn/phiên bản/duyệt; tách rõ lexical development baseline khỏi
   semantic embeddings nghiên cứu. Không có kho được duyệt thì trả rỗng.
5. EviOCEAN: job có quyền, bằng chứng nhiều cuộc trò chuyện, adapter chưa cấu
   hình trả không kết luận; không suy ra trait bằng từ khóa. Không có predictor,
   trọng số hay benchmark Việt thì ghi thiếu và không tuyên bố tái lập.
6. Công cụ nhận ca: vai trò cấp bằng CLI cục bộ, quyền chia sẻ riêng, tóm tắt do
   người dùng duyệt, trạng thái pending/accepted/in_progress/resolved/declined/
   unavailable/out_of_hours. Chỉ accepted sau thao tác xác nhận của chuyên gia.
7. Vận hành: production fail closed về khóa/cookie, health/readiness, audit
   không nội dung, số liệu tổng hợp, cleanup worker, backup nhất quán và restore
   vào thư mục mới, hướng dẫn rollback giữ snapshot tương ứng schema.

## Kiểm chứng

- Baseline: 35 backend tests pass trước thay đổi.
- Viết và chạy test thất bại cho tài khoản/quyền/migration/an toàn trước code.
- Kiểm thử hợp đồng nghiên cứu, truy hồi không dùng sample ở production,
  lỗi AI và đầu ra bị giữ lại; không gọi model thật trong suite.
- Build TypeScript và Playwright cho đăng ký/đăng nhập/thu hồi/khôi phục chat,
  các luồng cũ và giao diện chuyên gia.
- Báo cáo riêng phần chạy được, phần cần chuyên môn/đối tác/dữ liệu/model thật.

## Ghi nhận nguồn

Đã trích toàn bộ ba PDF vào research/paper-text để đối chiếu phương pháp.
Kho upstream có Mind-Reframe, Mind-Reframe-v2, Lumina; không có CARE hoặc
EviOCEAN. CogRAG PDF trỏ github.com/CogAI-Lab/CogRAG; truy cập web ban đầu
không lấy được nội dung. Chưa coi kho đó đã tải hoặc kiểm chứng.
