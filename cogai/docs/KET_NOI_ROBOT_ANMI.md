# Nối robot Ricky với AnMi — 26/10/2026

> Cập nhật 31/10/2026: đã build và nạp AnMi 2.5.3 vào thiết bị Ricky mới,
> MAC `14:c1:9f:c6:e0:44`, COM11. Hash ghi flash đã được xác minh; robot
> khởi động vào cấu hình Wi-Fi `Xiaozhi-E045`. Xem
> [biên bản nạp và bước cấu hình còn lại](NAP_ROBOT_ANMI_20261031.md).
> Các trạng thái “chưa có .bin/chưa nạp” bên dưới là lịch sử của lần làm trước.

> Cập nhật 27/10/2026: người vận hành yêu cầu dọn môi trường build nặng.
> Đã dừng/xóa container và image `cogai/ricky-builder:local`, xóa riêng 9,037 GB
> cache build Ricky và thư mục `F:\DELL\CogAI-Ricky-build` (1.728 GB).
> Mã nguồn board/GPIO, firmware gốc và CogAI được giữ nguyên. Chưa xuất `.bin`.
> Các lệnh Docker bên dưới là cách build cũ, không chạy lại khi chỉ cần thử GPIO.
> Kế hoạch tiếp theo là kiểm tra từng phần cứng với bộ công cụ chỉ cho ESP32-S3.
> Chi tiết dọn: `firmware/output-ricky-20261026/cleanup-report.json`.

## Trạng thái bàn giao

Cổng OTA `/xiaozhi/ota/` và WebSocket `/xiaozhi/v1/` đã có. Robot gửi Opus
16 kHz mono, khung 60 ms; backend nhận giọng, chạy cùng pipeline AnMi với web,
rồi gửi giọng AnMi dưới dạng Opus 24 kHz mono. Không lưu âm thanh.
Token được mã hóa trên đĩa; WebSocket kiểm tra token và MAC. Mỗi kết nối có
phiên khách riêng, xóa khi ngắt kết nối; không liên kết tài khoản web.

Đăng ký thiết bị hiện được coi là xác nhận của người vận hành rằng người thử
đã đồng ý xử lý giọng nói và gửi nội dung tới AI ngoài, là người trưởng thành.
Chưa có màn hình đồng ý riêng trên robot. Chỉ dùng với người thử đã được thông
báo và đồng ý; không dùng robot chung để tự thu âm người chưa đồng ý.

OTA cấp token theo MAC đã đăng ký, vì vậy cổng này chỉ dành cho LAN tin cậy.
Chưa đưa OTA lên Internet hoặc Kaggle. Chưa triển khai liên kết tài khoản
hoặc điều khiển motor/MCP. Firmware có câu báo mất kết nối ghi sẵn bằng giọng
HoaiMy, không cần mạng để phát; không tự chèn số hỗ trợ khi chưa xác minh.

## Chạy trên laptop

Từ thư mục workspace:

```powershell
node cogai/scripts/dev.mjs --live --device
```

Backend tự đọc API key đã có trong `cogai/backend/.env`. Launcher không in key
và không tự gọi dịch vụ AI khi khởi động. Web: `http://127.0.0.1:5173`.
API lắng nghe LAN trên cổng 8000. Terminal in địa chỉ OTA; máy có VPN hoặc nhiều
card mạng cần chọn địa chỉ Wi-Fi thật. Cho phép cổng 8000 trên mạng riêng nếu
Windows Firewall đang chặn. Laptop và robot phải ở cùng mạng.

Đăng ký station MAC thật của robot từ terminal khác:

```powershell
cd cogai/backend
.venv/Scripts/python.exe -m app.devices add aa:bb:cc:dd:ee:ff "Ricky AnMi"
.venv/Scripts/python.exe -m app.devices list
```

Địa chỉ trên là ví dụ, không phải MAC thật. Token chỉ in khi đăng ký; không gửi
token vào chat. Chạy `add` lần nữa sẽ đổi token và vô hiệu token cũ.
Nếu launcher dùng `--demo-data`, CLI phải dùng cùng `COGAI_DATA_DIR`.

Nhập OTA URL `http://<IP Wi-Fi laptop>:8000/xiaozhi/ota/` trong trang cấu hình
Wi-Fi robot. Firmware lấy token qua OTA; bấm nút GPIO0 để bắt đầu nói.
Chưa kiểm chứng thao tác này trên robot thật; máy hiện không thấy cổng ESP32 USB.

## Firmware

Nguồn nằm tại `cogai/firmware/xiaozhi-esp32`, sao chép từ upstream revision
`c435f99a88066029ec2dbd2d758c8cc9d051565b`. Script `prepare_ricky.py` dựng lại
board riêng mà không sửa sơ đồ chân board gốc. Chọn USB Serial/JTAG thay UART
vì GPIO43/44 là chân motor. Motor không có lệnh vận hành và được giữ LOW.
Nếu OLED không trả lời ở 0x3C, firmware dùng NoDisplay để vẫn khởi tạo audio.

Sau khi người vận hành dọn ổ C, Docker đã được phục hồi bằng khởi động lại
Docker Desktop và WSL. Image ESP-IDF 6.1 đã tạo thành công. Thư viện,
cache và thư mục biên dịch đặt tại `F:\DELL\CogAI-Ricky-build`, giữ dung lượng
ổ C cho Docker. Chưa đổi nơi lưu trữ image/volume Docker hiện có.

Từ thư mục firmware source, lệnh build dùng lại cache trên F:

```powershell
docker build --build-arg FIRMWARE_SOURCE_REVISION=c435f99a88066029ec2dbd2d758c8cc9d051565b -f docker/firmware-builder/Dockerfile -t cogai/ricky-builder:local .
$outputPath = Join-Path (Get-Location) '../output-ricky-20261026'
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
$outputPath = (Resolve-Path -LiteralPath $outputPath).Path
$cacheRoot = 'F:\DELL\CogAI-Ricky-build'
New-Item -ItemType Directory -Force -Path "$cacheRoot\build","$cacheRoot\managed_components","$cacheRoot\cache" | Out-Null
docker run --rm --cpus 4 -e FIRMWARE_BOARD_DIR=ricky-war-tank -e FIRMWARE_BOARD_NAME=ricky-war-tank -e FIRMWARE_LANGUAGE=vi-VN -e FIRMWARE_WAKE_WORD=disabled --mount "type=bind,source=$cacheRoot\build,target=/opt/xiaozhi-esp32/build" --mount "type=bind,source=$cacheRoot\managed_components,target=/opt/xiaozhi-esp32/managed_components" --mount "type=bind,source=$cacheRoot\cache,target=/root/.cache" --mount "type=bind,source=$outputPath,target=/output" cogai/ricky-builder:local
```

Giữ kiến trúc mặc định của Docker Desktop trên laptop. Chưa nạp firmware.
Cần build thành công và kiểm tra mic/loa, mất mạng, kích thước OLED trên phần
cứng trước khi nghiệm thu. Chỉ nạp khi được người vận hành đồng ý.

## Kiểm chứng

Đã chạy server live: web và `/api/health` trả HTTP 200; một lượt chat kỹ thuật
với AI thật trả HTTP 200 và phản hồi có nội dung. Phiên thử không lưu lịch sử
và đã được xóa. OTA không có đăng ký trả HTTP 403 đúng thiết kế.
Toàn bộ backend ở bản cuối đạt 121/121 ca, gồm 10 ca robot. Chỉ có cảnh báo
deprecation của TestClient.
Launcher đã bỏ cách chọn địa chỉ mạng đầu tiên, hiển thị tên từng card để tránh
trỏ nhầm VPN. Địa chỉ Wi-Fi lúc kiểm tra: `192.168.1.188` (có thể đổi theo DHCP).

Firmware: bộ host test chạy lại trong Linux có 143 ca, không lỗi, 3 ca bỏ qua
vì thiếu thư viện kiểm thử tùy chọn (cJSON/mbedTLS, numpy/Pillow/packaging).
Log tại `firmware/output-ricky-20261026/host-tests-final.log`. Lỗi môi trường Windows
trong log cũ không dùng làm kết quả nghiệm thu firmware.
Clip “Mất kết nối.” được kiểm tra bằng chính OggDemuxer của firmware: 16 gói
Opus mono, 24 kHz, 60 ms, không lỗi, nằm trong bộ đệm 1,2 giây để không chặn
vòng lặp chính. Script `firmware/verify_offline_voice.py`
chạy trong Linux; script `make_offline_voice.py` tạo lại bản ghi bằng Edge TTS.

Kiểm thử transport dùng Opus thật và provider giả lập, không gọi API trả phí:
đăng ký/đổi/xóa token, OTA, xác thực MAC, bắt tay, hai lượt liên tiếp,
transcript rỗng, lỗi xử lý, dữ liệu sai, phiên mới và giới hạn bộ đệm.
Các kiểm thử này không xác nhận chất lượng mic/loa, giọng dịch vụ thật,
biểu cảm, motor hoặc khả năng kết nối của robot vật lý.
