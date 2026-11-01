# Build firmware AnMi Ricky

Gói này chỉ chứa mã nguồn firmware. Không chứa bản sao lưu robot, mật khẩu
Wi-Fi, token thiết bị hay khóa AI. SDK chạy trên GitHub Actions, không cần cài
Docker hoặc ESP-IDF trên laptop. Chưa có file `.bin` trước khi workflow chạy đạt.

## Lấy firmware

1. Tạo repository GitHub riêng cho firmware (khuyến nghị private).
2. Giải nén gói source trên máy. Đưa toàn bộ nội dung đã giải nén lên root của
   repository, gồm `.github/workflows/build-anmi.yml`, `firmware/` và
   `SOURCE_MANIFEST.json`. Không upload nguyên ZIP rồi mong Actions tự chạy.
3. Trong repository, mở Actions → Build AnMi Ricky → Run workflow.
4. Khi job thành công, tải artifact `anmi-ricky-n16r8-…`.
5. Giữ `merged-binary.bin`, `xiaozhi.bin`, `manifest.json`, `verification.json`
   và log. Gửi kết quả build cho người hỗ trợ kiểm tra trước khi nạp.

Workflow chỉ build ESP32-S3 board `ricky-war-tank`, tiếng Việt, không từ đánh
thức. Không publish firmware và không tự nạp thiết bị. Cần tài khoản GitHub,
Actions được bật và đủ hạn mức của tài khoản; không tự bật dịch vụ trả phí.
Nếu bạn sửa source, hãy tạo lại source package/manifest để hash khớp.

## Cấu hình sau khi đã kiểm tra và được phép nạp

Firmware dùng mic WS4/SCK5/DIN6, loa DOUT7/BCLK15/LRCK16, LED48, nút0.
Các chân motor39/40/43/44 giữ LOW. Console chỉ qua USB Serial/JTAG.
OLED 128x64 trên SDA41/SCL42 là tùy chọn; lỗi OLED không được ngăn audio chạy.
Giữ nút BOOT 2 giây sau khi khởi động để mở cấu hình Wi-Fi; bấm ngắn để trò
chuyện khi server đã sẵn sàng. Không giữ BOOT trong lúc cấp nguồn.

Nhập Wi-Fi 2,4 GHz trong trang cấu hình của robot. OTA mặc định hiện là
`https://<NGROK_DOMAIN>/xiaozhi/ota/` cho server Kaggle (tự điền tên miền riêng).
Muốn dùng backend trên laptop, đổi OTA URL thành
`http://<IP Wi-Fi laptop>:8000/xiaozhi/ota/`. Không gửi mật khẩu cho người hỗ trợ.
Board tự bỏ giá trị OTA cũ `http://anmi.local:8000/xiaozhi/ota/` nếu đã lưu;
cấu hình Wi-Fi và các OTA tùy chỉnh khác được giữ nguyên.

Tại dự án CogAI trên laptop:

```powershell
node cogai/scripts/dev.mjs --live --device
```

Đăng ký MAC robot với cùng data directory của backend trước khi robot gọi OTA.
Không đưa token vào firmware source hay repository. Backend xác thực MAC + token.
Chỉ thử trên LAN tin cậy với người trưởng thành đã đồng ý gửi âm thanh tới AI.

## Nghiệm thu thực tế

Build thành công chưa chứng minh GPIO đúng hoặc phần cứng hoạt động.
Cần thử mic/loa, kết nối Wi-Fi, ít nhất 3 lượt AnMi liên tiếp, ngắt lời,
mất/kết nối lại mạng và xác nhận motor không chuyển động. Giữ bản backup ở
máy riêng; không upload backup vào repository hoặc Actions.
