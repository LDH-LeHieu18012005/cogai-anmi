# CogAI / AnMi

Mã nguồn web, backend và firmware cho hệ sinh thái CogAI. Xem
[hướng dẫn chạy dự án](cogai/README.md).

## Giữ phiên bản robot

Các bản firmware và bản sao flash được giữ tại máy trong
`cogai/firmware/output-ricky-*/`, `cogai/firmware/backups/` và tệp firmware gốc
ở thư mục gốc. Không đưa những tệp này lên GitHub: flash có thể chứa Wi-Fi,
token và dữ liệu thiết bị. Không nạp lại robot chỉ vì vừa dọn dự án.

Theo biên bản ngày 31/10, bản RSA là bản sửa kết nối đã được nạp cho robot
mới; robot còn lại sử dụng firmware gốc. Đây là thông tin từ tài liệu và log,
không phải kết quả đọc trực tiếp hai robot trong đợt dọn này. Giữ tất cả các
bản hiện có để tránh mất bản đang dùng. Chi tiết bảo toàn và khôi phục nằm ở
[biên bản dọn dự án](cogai/docs/DON_DEP_2026_11_02.md).

## Chuẩn bị đưa mã nguồn lên GitHub

Từ thư mục gốc, chạy:

```powershell
& cogai/backend/.venv/Scripts/python.exe cogai/scripts/prepare-publication.py
& cogai/backend/.venv/Scripts/python.exe cogai/scripts/prepare-publication.py --export
```

Máy mới có thể dùng Python 3.12+ thay cho đường dẫn `.venv` trên. Lệnh chỉ
kiểm tra và tạo `dist/github-source-2026-11-02.zip`, không upload, không gọi AI
và không truy cập robot. Gói ZIP chứa mã nguồn đã lọc; giải nén sang thư mục
riêng rồi đưa nội dung đó vào repository mới. Không upload cả thư mục dự án
gốc hay ZIP sao lưu. Mỗi lần sửa mã, chạy lại kiểm tra và tạo lại gói.

`.gitignore` giữ riêng `.env`, khóa, database, token, firmware, backup,
cache, các gói triển khai và hồ sơ dự thi/nghiên cứu chưa duyệt công khai.
Hai tệp `.env.example` và `.env.production.example` là mẫu được giữ lại.
Kiểm tra tự động không thay thế việc duyệt nội dung trước khi công khai;
không phân tích lịch sử Git trên máy chủ.

Cấu hình build Ricky đang chạy được giữ riêng tại máy để không lộ endpoint.
Gói công khai dùng `config.json` sinh từ `config.public.example.json`, vẫn giữ
cấu hình TLS RSA nhưng dùng địa chỉ mẫu `example.invalid`. Trước khi build
cho máy mới, điền endpoint riêng vào `config.json`. Nếu clone trực tiếp mã
nguồn thay vì dùng ZIP, sao chép mẫu thành `config.json` trong thư mục board
`cogai/firmware/xiaozhi-esp32/main/boards/ricky-war-tank/` trước khi build.

Nếu khóa từng được công khai ở nơi khác, cần thay khóa đó và xử lý lịch sử
repository tương ứng. `.gitignore` không xóa thông tin đã từng được commit.
