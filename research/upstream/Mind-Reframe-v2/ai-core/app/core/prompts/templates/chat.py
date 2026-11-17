from app.core.prompts.base import PromptTemplate

# Template cho general chat
GENERAL_CHAT_TEMPLATE = PromptTemplate(
    template="{user_message}",
    required_vars=["user_message"],
    temperature=0.7,
    max_tokens=1000,
    system_prompt="Bạn là một AI assistant thân thiện và hữu ích. Hãy trả lời câu hỏi một cách rõ ràng và chính xác."
)

# Template cho customer support
CUSTOMER_SUPPORT_TEMPLATE = PromptTemplate(
    template="""
Khách hàng: {customer_name}
Vấn đề: {issue}
Chi tiết: {details}

Hãy phân tích và đưa ra giải pháp cho vấn đề trên.
""".strip(),
    required_vars=["customer_name", "issue", "details"],
    temperature=0.5,
    max_tokens=800,
    system_prompt="Bạn là một chuyên viên customer support chuyên nghiệp. Hãy phân tích vấn đề và đưa ra giải pháp cụ thể, rõ ràng."
)

# Template cho code explanation
CODE_EXPLANATION_TEMPLATE = PromptTemplate(
    template="""
Ngôn ngữ: {language}
Code:
```{language}
{code}
```

Hãy giải thích đoạn code trên một cách chi tiết.
""".strip(),
    required_vars=["language", "code"],
    temperature=0.3,
    max_tokens=1500,
    system_prompt="Bạn là một lập trình viên giàu kinh nghiệm. Hãy giải thích code một cách dễ hiểu, từng bước một."
)

# Template cho translation
TRANSLATION_TEMPLATE = PromptTemplate(
    template="""
Dịch văn bản sau từ {source_lang} sang {target_lang}:

{text}
""".strip(),
    required_vars=["source_lang", "target_lang", "text"],
    temperature=0.3,
    max_tokens=2000,
    system_prompt="Bạn là một dịch giả chuyên nghiệp. Hãy dịch chính xác và giữ nguyên ý nghĩa của văn bản gốc."
)