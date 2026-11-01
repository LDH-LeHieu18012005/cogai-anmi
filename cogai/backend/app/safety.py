import re
import unicodedata

from .models import Risk
from .identity import ASSISTANT_NAME


def normalize(text: str):
    text = unicodedata.normalize("NFD", text.casefold()).replace("đ", "d")
    return re.sub(r"\s+", " ", "".join(c for c in text if unicodedata.category(c) != "Mn"))


def rule_risk(text: str) -> Risk:
    # Preserve this common accented distinction before diacritic folding:
    # "từ từ" (slowly) must not become "tự tử" (suicide).
    disambiguated = re.sub(r"\btừ\s+từ\b", "chậm rãi", text.casefold())
    value = normalize(disambiguated)
    # Conservative development rules. These are not a validated clinical classifier.
    urgent = [r"\btu\s*(tu|sat|hai)\b", r"\bmuon chet\b", r"\bket thuc cuoc doi\b",
              r"\blam hai (ban than|minh|nguoi khac)\b", r"\bgiet (minh|nguoi|ai do)\b",
              r"\bkhong muon (tiep tuc )?song\b", r"\buong.*qua lieu\b", r"\b(suicid\w*|self[ -]?harm)\b",
              r"\b(kill myself|end my life|hurt myself|want to die)\b"]
    if any(re.search(pattern, value) for pattern in urgent):
        return Risk(level="high", reason="Có nội dung cần ưu tiên kiểm tra an toàn; đây chưa phải kết luận lâm sàng.", source="rules", requires_support=True)
    # "không muốn tiếp tục học/làm ..." names what to stop; only the bare phrase is ambiguous.
    ambiguous = [r"\bkhong muon tiep tuc( nua)?\s*([.!?,…]|$)", r"\bbien mat mai mai\b", r"\bhet ly do\b",
                 r"\bkhong chiu noi nua\b"]
    if any(re.search(pattern, value) for pattern in ambiguous):
        return Risk(level="check_in", reason="Chưa rõ ý nghĩa của lời chia sẻ; cần hỏi thêm về sự an toàn.", source="rules", requires_support=True)
    return Risk(level="low", reason="Quy tắc thử nghiệm chưa phát hiện tín hiệu ưu tiên; điều này không xác nhận không có nguy cơ.", source="rules")


def redact(text: str):
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    text = re.sub(r"(?<!\w)(?:\+?84|0)(?:[ .-]?\d){8,10}(?!\w)", "[SỐ ĐIỆN THOẠI]", text)
    return text


SUPPORT_REPLY = (
    "Cảm ơn bạn đã nói với mình. Mình muốn ưu tiên sự an toàn của bạn lúc này. "
    "Bạn có đang gặp nguy hiểm ngay lúc này không? Nếu có, hãy gọi cấp cứu 115 "
    "hoặc nhờ một người bạn tin tưởng ở gần đến ở cùng. "
    "Mình là AI và không thể tự gọi hay cử người đến. Bạn có thể mở mục Hỗ trợ để xem các lựa chọn."
)
CHECK_IN_REPLY = (
    "Mình muốn chắc là mình hiểu đúng ý bạn. Điều bạn vừa nói là về một việc đang làm bạn kiệt sức, "
    "hay bạn đang nghĩ đến việc làm hại bản thân hoặc không muốn sống nữa? Bạn cứ nói thật, mình vẫn "
    "ở đây lắng nghe. Nếu bạn đang thấy không an toàn, hãy gọi 115 hoặc nhờ một người tin tưởng ở gần."
)
RETRY_REPLY = f"Xin lỗi, {ASSISTANT_NAME} vừa gặp trục trặc nhỏ khi trả lời. Bạn nói lại giúp mình được không?"
UNAVAILABLE_REPLY = (
    "Mình chưa kiểm tra được đầy đủ để tiếp tục phần gợi ý lúc này. Bạn có thể thử lại sau. "
    "Nếu bạn đang không an toàn, hãy tìm một người tin tưởng ở gần hoặc dịch vụ cấp cứu tại nơi bạn sống."
)


# Fixed wording: nothing to generate or check, and the same on web and robot voice.
OFF_TOPIC_REPLIES = (
    f"Mình là {ASSISTANT_NAME}, trợ lý chỉ hỗ trợ chăm sóc sức khỏe tinh thần, nên không giúp được câu hỏi này. "
    "Bạn có thể tìm cách giải quyết khác phù hợp hơn nhé. Nếu đang có điều gì làm bạn mệt mỏi, mình sẵn sàng lắng nghe.",
    "Xin lỗi bạn, mình chỉ lắng nghe và hỗ trợ về cảm xúc, tâm lý thôi. Với việc này, bạn thử tìm nguồn hoặc "
    "người có chuyên môn phù hợp hơn nhé. Còn nếu muốn kể về cảm xúc của mình, mình ở đây.",
    f"Phần này mình không hỗ trợ được, vì {ASSISTANT_NAME} chỉ tập trung vào sức khỏe tinh thần. "
    "Bạn có thể tìm phương pháp khác cho vấn đề đó. Hôm nay bạn đang cảm thấy thế nào?",
)


def off_topic_reply(history):
    # Rotate so a user who keeps asking does not hear the same sentence back to back.
    previous = next((t["content"] for t in reversed(history) if t.get("role") == "assistant"), None)
    index = OFF_TOPIC_REPLIES.index(previous) + 1 if previous in OFF_TOPIC_REPLIES else 0
    return OFF_TOPIC_REPLIES[index % len(OFF_TOPIC_REPLIES)]


def support_reply(risk: Risk):
    if risk.level == "high":
        return SUPPORT_REPLY
    if risk.level == "check_in":
        return CHECK_IN_REPLY
    return UNAVAILABLE_REPLY
