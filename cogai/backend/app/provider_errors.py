"""Public operator guidance derived only from status codes, never provider bodies."""
from fastapi import HTTPException


def service_error(status):
    guidance={
        401:'Dịch vụ AI từ chối xác thực (401). Hãy tự kiểm tra khóa trong backend/.env và khởi động lại CogAI. Không gửi khóa vào hội thoại.',
        403:'Dịch vụ AI từ chối quyền truy cập (403). Hãy kiểm tra quyền của khóa và dự án tại nhà cung cấp.',
        404:'Dịch vụ AI không tìm thấy endpoint hoặc model (404). Hãy kiểm tra model và cấu hình nhà cung cấp.',
        429:'Dịch vụ AI báo giới hạn yêu cầu hoặc hạn mức tài khoản (429). Hãy kiểm tra tài khoản tại nhà cung cấp; CogAI không tự thử lại.',
    }
    return HTTPException(503,guidance.get(status,'Dịch vụ AI tạm thời chưa sẵn sàng. Cuộc gọi đã dừng, không tự thử lại.'),
                         headers={'X-CogAI-Provider-Status':str(status)})
