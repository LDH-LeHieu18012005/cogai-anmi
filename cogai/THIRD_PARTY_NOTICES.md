# Tài sản kế thừa

## Firmware XiaoZhi

Nguồn [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32), revision
`c435f99a88066029ec2dbd2d758c8cc9d051565b`, được sao chép tại
`firmware/xiaozhi-esp32` để chuẩn bị board Ricky riêng. Giữ nguyên tệp LICENSE
và thông báo nguồn trong bản sao. Các thay đổi của CogAI gồm board
`ricky-war-tank`, đăng ký board trong Kconfig/CMake và hook âm thanh báo lỗi
mạng tùy chọn qua giao diện Board. Chưa xác minh phần cứng.
`firmware/prepare_ricky.py` tái tạo board và đăng ký cấu hình. Clip “Mất kết nối.”
được tạo bằng Edge HoaiMy và đóng gói riêng trong board Ricky.

## edge-tts (giọng đọc tiếng Việt)

Gói Python [edge-tts](https://github.com/rany2/edge-tts) 7.3.1, giấy phép LGPLv3, được
dùng như thư viện không sửa đổi để gọi dịch vụ đọc của Microsoft Edge với giọng
`vi-VN-HoaiMyNeural`. Đây là dịch vụ không chính thức, không có SLA; văn bản phản
hồi (đã che email/số điện thoại) được gửi tới Microsoft. Trước khi thương mại hóa,
cần chuyển sang Azure AI Speech có hợp đồng (cùng họ giọng `vi-VN-*Neural`) hoặc
được tư vấn pháp lý xác nhận.

## Tham khảo AIRI cho trải nghiệm tác nhân

[Project AIRI](https://github.com/moeru-ai/airi), trang https://airi.moeru.ai/,
được tham khảo về nhân vật, tách renderer/provider giọng nói và vòng đời hủy
âm thanh. LICENSE của upstream ghi MIT, copyright 2024–PRESENT Neko Ayaka.
Đợt triển khai này không sao chép mã AIRI, không đóng gói engine hay model
Live2D/VRM/nhân vật của họ; `Companion.tsx`, `AgentChat.tsx`, `useVoice.ts` và
SVG/CSS Mầm được viết riêng cho CogAI. Không tuyên bố là tích hợp AIRI đầy đủ.

## Mind-Reframe và Lumina

Người dùng xác nhận trong phiên làm việc ngày 22/10/2026 rằng Mind-Reframe/Lumina là mã của nhóm mình và cho phép dùng để phát triển CogAI.

Nguồn trực tiếp:

- [Mind-Reframe](https://huggingface.co/spaces/Anonymous-EmpathyAI/Mind-Reframe/tree/main), revision `fb1ada96ac089d2e91e9fb2d41140dd5cf8ede67`.
- [Mind-Reframe-v2](https://huggingface.co/spaces/Anonymous-EmpathyAI/Mind-Reframe-v2/tree/main), revision `3dace8bad1eb73ec75deec7fa800376bc8cf83a9`.
- [Lumina](https://huggingface.co/spaces/Anonymous-EmpathyAI/Lumina/tree/main), revision `0d1e8ced754b4cc0d9ebce5067aef71852752936`.

Space card của cả ba ghi `apache-2.0`. README bên trong `ai-core` lại có nhãn MIT; cần nhóm thống nhất thông tin giấy phép trước khi phát hành ra ngoài. Không tự suy ra một giấy phép mới cho toàn bộ CogAI từ các nhãn khác nhau này.

`backend/app/legacy/base.py` được sao chép từ `Lumina/ai-core/app/core/prompts/base.py`. `backend/app/legacy/reframe.py` được sao chép từ `Lumina/ai-core/app/core/prompts/templates/reframe.py`, chỉ thay đường dẫn import sang `app.legacy.base`. Luồng live sử dụng trực tiếp các template CBT, ACT và CFT, bao bọc bởi chính sách và schema đầu ra của CogAI. Các template khác được giữ nguyên để bảo toàn nguồn nhưng không được mở qua API.

Luồng DoT, tạo nhiều góc nhìn, nhận xét và sửa theo phản hồi được điều chỉnh từ thiết kế của Mind-Reframe/Lumina. Backend phiên/lưu trữ/kiểm tra, giao diện CogAI, kiểm thử và cấu hình Docker mới được viết trong lần triển khai này.

65 tệp nguồn chọn lọc của mỗi Space được giữ trong `../research/upstream/`. Mỗi thư mục có `SOURCE_MANIFEST.json` ghi revision và SHA-256 từng tệp. Các tệp môi trường, log, dữ liệu phản hồi, file biên dịch và tài sản nhị phân không được tải vào bản tham chiếu.

Bảng hỏi PHQ/GAD: hướng dẫn của tác giả nêu các công cụ thuộc public domain, xem [Instruction Manual, trang 8](https://www.uab.edu/medicine/pcp-sci/images/SCIMS/PHQ-9_Instruction_Manual.pdf). Bản Việt hóa trong CogAI là nháp phục vụ phát triển, không tự nhận là bản dịch đã kiểm định. Người phát triển cần chọn và xác minh bản tiếng Việt phù hợp với cố vấn trước khi thí điểm.
