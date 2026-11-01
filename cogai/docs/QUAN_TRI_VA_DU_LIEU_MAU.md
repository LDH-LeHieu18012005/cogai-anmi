# Trang quản trị và dữ liệu mẫu

## Chạy với dữ liệu mẫu

```powershell
Set-Location "C:\Users\DELL\Desktop\CogAI Hệ sinh thái AI sàng lọc sớm và hỗ trợ sức khỏe tinh thần"
node cogai/scripts/dev.mjs --demo-data          # thêm --live nếu muốn AI thật
```

Lần đầu, launcher tạo `backend/data-demo` (dữ liệu thật ở `backend/data` không bị
động tới). Tạo lại từ đầu: `cd cogai/backend` rồi
`.\.venv\Scripts\python.exe -m app.seed_demo --reset`.

Mở http://127.0.0.1:5173 → "Đã có tài khoản bí danh? Đăng nhập". Mật khẩu chung
`cogai2026demo`:

| Bí danh | Vai trò | Xem được |
|---|---|---|
| `admin` | Quản trị | Mục **Quản trị**: tổng quan, tài khoản, hỗ trợ & an toàn, nhật ký |
| `expert` | Chuyên gia | Mục **Tiếp nhận hỗ trợ**: hàng đợi, tiếp nhận/xử lý/đóng ca |
| `user` | Người dùng | 45 ngày tâm trạng, sàng lọc, trò chuyện, bài tập; nhật ký |
| `dna-01`… `sv-22`, `tn-01..03` | Người dùng | 67 người mẫu thuộc 4 nhóm tổ chức |

Toàn bộ là dữ liệu tổng hợp: người, tổ chức (có chữ "mẫu") và câu chữ đều được
tạo ra, không phải dữ liệu sức khỏe thật. Nhóm "Nhóm thử nghiệm nhỏ (mẫu)" chỉ có
3 người để minh họa việc ẩn báo cáo nhóm nhỏ.

## Trang Quản trị làm gì

Theo thuyết minh (bảng 1, mục 2): tổ chức chỉ nhận **số liệu tổng hợp ẩn danh,
chỉ hiển thị khi nhóm đủ đông**.

- **Tổng quan** (lọc theo nhóm tổ chức, 7/30/90 ngày): người dùng, hoạt động 7
  ngày, tỷ lệ đã sàng lọc (chỉ số thí điểm ≥ 70%), lượt trò chuyện/tâm trạng;
  biểu đồ người hoạt động và tâm trạng trung bình theo ngày; phân bố PHQ-9/GAD-7
  gần nhất; phân bố tâm trạng; tỷ lệ đồng ý theo mục đích. Mỗi biểu đồ có bảng số.
- **Tài khoản**: tìm kiếm, lọc vai trò; đổi vai trò người dùng ↔ chuyên gia và gán
  nhóm tổ chức. Chỉ xem số lượng bản ghi, không xem nội dung.
- **Hỗ trợ & an toàn**: số tín hiệu nguy cơ cao / cần hỏi lại, PHQ-9 câu 9, thời
  gian phản hồi trung vị, yêu cầu hỗ trợ theo trạng thái (không có tóm tắt).
- **Nhật ký hoạt động**: hành động và thời điểm, không có nội dung.

Nguyên tắc riêng tư: nhóm hoặc mức có dưới `COGAI_AGGREGATE_MIN_GROUP` (mặc định
5) người hiển thị "< 5"; admin không đọc được trò chuyện, ghi chú tâm trạng hay
tóm tắt hỗ trợ; mọi lần xem/đổi được ghi nhật ký. Quyền quản trị chỉ cấp bằng
công cụ vận hành, không cấp qua web:

```powershell
cd cogai/backend
.\.venv\Scripts\python.exe -m app.operations grant-admin <bí-danh>
.\.venv\Scripts\python.exe -m app.operations revoke-admin <bí-danh>
```

Với dữ liệu thật (không dùng `--demo-data`), hãy tạo tài khoản bí danh trên web rồi
chạy lệnh trên (thêm `$env:COGAI_DATA_DIR` nếu dùng thư mục khác).

## Chưa có

Người dùng chưa tự chọn nhóm tổ chức (khi thí điểm nên dùng mã mời của tổ
chức); chưa xuất báo cáo PDF/Excel cho tổ chức; chưa có đo PSS-10 sau 8 tuần.
