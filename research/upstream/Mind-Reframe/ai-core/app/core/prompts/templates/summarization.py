from app.core.prompts.base import PromptTemplate

# Template cho text summarization
TEXT_SUMMARY_TEMPLATE = PromptTemplate(
    template="""
Tóm tắt văn bản sau thành {length} câu:

{text}
""".strip(),
    required_vars=["text", "length"],
    temperature=0.5,
    max_tokens=500,
    system_prompt="Bạn là một chuyên gia tóm tắt văn bản. Hãy nắm bắt ý chính và tóm tắt một cách súc tích, rõ ràng."
)

# Template cho meeting notes
MEETING_NOTES_TEMPLATE = PromptTemplate(
    template="""
Hãy tóm tắt cuộc họp sau đây theo format:

**Mục đích cuộc họp:**
**Những điểm chính:**
**Action items:**
**Deadline:**

Nội dung cuộc họp:
{meeting_content}
""".strip(),
    required_vars=["meeting_content"],
    temperature=0.4,
    max_tokens=1000,
    system_prompt="Bạn là một trợ lý hành chính chuyên nghiệp. Hãy tóm tắt cuộc họp một cách có cấu trúc và đầy đủ thông tin quan trọng."
)

# Template cho article summary
ARTICLE_SUMMARY_TEMPLATE = PromptTemplate(
    template="""
Tóm tắt bài viết sau với độ dài khoảng {word_count} từ:

Tiêu đề: {title}
Nội dung:
{content}
""".strip(),
    required_vars=["title", "content", "word_count"],
    temperature=0.5,
    max_tokens=800,
    system_prompt="Bạn là một biên tập viên chuyên nghiệp. Hãy tóm tắt bài viết một cách khách quan, nắm bắt được các ý chính."
)