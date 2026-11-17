from typing import Dict, Optional
from app.core.prompts.base import PromptTemplate
from app.core.prompts.templates import chat, summarization, extraction, reframe, DoT

class PromptManager:
    """
    Manager class để quản lý và sử dụng prompt templates
    """
    
    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load tất cả default templates"""
        # Chat templates
        self.register("chat.general", chat.GENERAL_CHAT_TEMPLATE)
        self.register("chat.customer_support", chat.CUSTOMER_SUPPORT_TEMPLATE)
        self.register("chat.code_explanation", chat.CODE_EXPLANATION_TEMPLATE)
        self.register("chat.translation", chat.TRANSLATION_TEMPLATE)
        
        # Summarization templates
        self.register("summarization.text", summarization.TEXT_SUMMARY_TEMPLATE)
        self.register("summarization.meeting", summarization.MEETING_NOTES_TEMPLATE)
        self.register("summarization.article", summarization.ARTICLE_SUMMARY_TEMPLATE)
        
        # Extraction templates
        self.register("extraction.info", extraction.INFO_EXTRACTION_TEMPLATE)
        self.register("extraction.entities", extraction.ENTITY_RECOGNITION_TEMPLATE)
        self.register("extraction.sentiment", extraction.SENTIMENT_ANALYSIS_TEMPLATE)

        self.register("reframe.cbt", reframe.CBT_SINGLE_TEMPLATE)
        self.register("reframe.act", reframe.ACT_SINGLE_TEMPLATE)
        self.register("reframe.mbct", reframe.MBCT_SINGLE_TEMPLATE)
        self.register("reframe.rebt", reframe.REBT_SINGLE_TEMPLATE)
        self.register("reframe.schema therapy", reframe.ST_SINGLE_TEMPLATE)
        self.register("reframe.narrative therapy", reframe.NT_SINGLE_TEMPLATE)
        self.register("reframe.sfbt", reframe.SFBT_SINGLE_TEMPLATE)
        self.register("reframe.mi", reframe.MI_SINGLE_TEMPLATE)
        self.register("reframe.cft", reframe.CFT_SINGLE_TEMPLATE)
        self.register("reframe.dbt", reframe.DBT_SINGLE_TEMPLATE)
        self.register("reframe.thera_supervisor_full", reframe.THERAPIST_SUPERVISOR_FULL_TEMPLATE)
        self.register("reframe.cbtwfeedback", reframe.REFRAME_wFEEDBACK_TEMPLATE)

        self.register("dot.analysis", DoT.DOT_ANALYSIS_TEMPLATE)
        self.register("dot.detection", DoT.DOT_DETECTION_TEMPLATE)
        self.register("dot.thera_rcm", DoT.THERAPIST_RCM_TEMPLATE)
        self.register("dot.thera_supervisor", DoT.THERAPIST_SUPERVISOR_TEMPLATE)
    
    def register(self, name: str, template: PromptTemplate):
        """
        Đăng ký một prompt template
        
        Args:
            name: Tên của template (format: category.name)
            template: PromptTemplate object
        """
        self._templates[name] = template
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """
        Lấy template theo tên
        
        Args:
            name: Tên của template
            
        Returns:
            PromptTemplate nếu tìm thấy, None nếu không
        """
        return self._templates.get(name)
    
    def list_templates(self, category: Optional[str] = None) -> list[str]:
        """
        List tất cả templates hoặc theo category
        
        Args:
            category: Category để filter (optional)
            
        Returns:
            List tên của templates
        """
        if category:
            return [
                name for name in self._templates.keys() 
                if name.startswith(f"{category}.")
            ]
        return list(self._templates.keys())
    
    def format_prompt(self, name: str, **kwargs) -> tuple[str, Dict]:
        """
        Format một prompt template với variables
        
        Args:
            name: Tên của template
            **kwargs: Variables để fill vào template
            
        Returns:
            Tuple (formatted_prompt, default_params)
            
        Raises:
            ValueError: Nếu template không tồn tại hoặc thiếu variables
        """
        template = self.get(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        
        formatted_prompt = template.format(**kwargs)
        default_params = template.get_default_params()
        
        return formatted_prompt, default_params
    
    def create_custom_template(
        self,
        template_name: str,
        template: str,
        required_vars: list[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ):
        """
        Tạo và đăng ký custom template
        
        Args:
            name: Tên của template
            template: Template string
            required_vars: Required variables
            temperature: Default temperature
            max_tokens: Default max_tokens
            system_prompt: System prompt
        """
        custom_template = PromptTemplate(
            template=template,
            required_vars=required_vars,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        self.register(template_name, custom_template)

# Singleton instance
prompt_manager = PromptManager()