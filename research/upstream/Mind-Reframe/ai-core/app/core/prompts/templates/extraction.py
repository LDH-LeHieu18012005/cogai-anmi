from app.core.prompts.base import PromptTemplate

# Template cho information extraction
INFO_EXTRACTION_TEMPLATE = PromptTemplate(
    template="""
Trích xuất thông tin sau từ văn bản:
{fields}

Văn bản:
{text}

Trả về kết quả dưới dạng JSON với các key: {fields}
""".strip(),
    required_vars=["fields", "text"],
    temperature=0.2,
    max_tokens=1000,
    system_prompt="Bạn là một chuyên gia phân tích dữ liệu. Hãy trích xuất thông tin chính xác từ văn bản và trả về dưới dạng JSON."
)

# Template cho entity recognition
ENTITY_RECOGNITION_TEMPLATE = PromptTemplate(
    template="""
Nhận diện các entities sau trong văn bản:
- Người (PERSON)
- Tổ chức (ORGANIZATION)
- Địa điểm (LOCATION)
- Ngày tháng (DATE)

Văn bản:
{text}

Trả về danh sách entities với format: [type]: entity
""".strip(),
    required_vars=["text"],
    temperature=0.1,
    max_tokens=800,
    system_prompt="Bạn là một hệ thống NER (Named Entity Recognition). Hãy nhận diện chính xác các entities trong văn bản."
)

# Template cho sentiment analysis
SENTIMENT_ANALYSIS_TEMPLATE = PromptTemplate(
    template="""
Phân tích cảm xúc (sentiment) của văn bản sau:

{text}

Trả về:
1. Sentiment: Positive/Negative/Neutral
2. Confidence score: 0-1
3. Lý do: Giải thích ngắn gọn
""".strip(),
    required_vars=["text"],
    temperature=0.3,
    max_tokens=500,
    system_prompt="Bạn là một chuyên gia phân tích cảm xúc. Hãy đánh giá sentiment của văn bản một cách chính xác và khách quan."
)