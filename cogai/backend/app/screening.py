from .models import ScreeningInput

SOURCE = "https://www.uab.edu/medicine/pcp-sci/images/SCIMS/PHQ-9_Instruction_Manual.pdf"
QUESTIONNAIRES = {
    "PHQ-9": [
        "Ít hứng thú hoặc ít thấy vui khi làm các việc.",
        "Cảm thấy buồn, chán nản hoặc tuyệt vọng.",
        "Khó ngủ, ngủ không yên hoặc ngủ quá nhiều.",
        "Cảm thấy mệt mỏi hoặc thiếu năng lượng.",
        "Chán ăn hoặc ăn quá nhiều.",
        "Cảm thấy bản thân tồi tệ, thất bại hoặc đã làm bản thân hay gia đình thất vọng.",
        "Khó tập trung vào việc gì đó, chẳng hạn đọc báo hoặc xem tivi.",
        "Cử động hoặc nói chậm đến mức người khác nhận thấy; hoặc bồn chồn, đứng ngồi không yên hơn thường lệ.",
        "Nghĩ rằng thà chết đi còn hơn hoặc nghĩ đến việc tự làm đau bản thân.",
    ],
    "GAD-7": [
        "Cảm thấy căng thẳng, lo âu hoặc bồn chồn.",
        "Không thể ngừng hoặc kiểm soát lo lắng.",
        "Lo lắng quá nhiều về nhiều việc khác nhau.",
        "Khó thư giãn.",
        "Bồn chồn đến mức khó ngồi yên.",
        "Dễ bực bội hoặc cáu gắt.",
        "Cảm thấy lo sợ như thể một điều khủng khiếp có thể xảy ra.",
    ],
}


def score_screening(data: ScreeningInput):
    expected = len(QUESTIONNAIRES[data.kind])
    if len(data.answers) != expected:
        raise ValueError(f"{data.kind} cần đủ {expected} câu trả lời.")
    total = sum(data.answers)
    thresholds = [5, 10, 15, 20] if data.kind == "PHQ-9" else [5, 10, 15]
    index = sum(total >= cut for cut in thresholds)
    bands = ["Tối thiểu", "Nhẹ", "Vừa", "Khá nặng", "Nặng"] if data.kind == "PHQ-9" else ["Tối thiểu", "Nhẹ", "Vừa", "Nặng"]
    needs_check = data.kind == "PHQ-9" and data.answers[8] > 0
    return {
        "kind": data.kind, "score": total, "maximum": expected * 3,
        "band": bands[index], "requires_support": needs_check,
        "message": "Đây là mức điểm của bảng hỏi, không phải chẩn đoán. Bản Việt hóa đang dùng cho phát triển và cần chuyên gia rà soát trước thí điểm.",
        "next_step": "Bạn nên trao đổi kết quả với người có chuyên môn." if total >= 10 or needs_check else "Bạn có thể ghi nhận cảm xúc và trao đổi với người có chuyên môn nếu vẫn thấy khó khăn.",
        "source": SOURCE, "version": "vi-draft-1", "difficulty": data.difficulty,
    }
