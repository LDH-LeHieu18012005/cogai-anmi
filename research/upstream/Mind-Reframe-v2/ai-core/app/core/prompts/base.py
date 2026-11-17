from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class BasePromptTemplate(ABC):
    """
    Base class cho prompt templates
    """
    
    def __init__(self, template: str, required_vars: list[str] = None):
        """
        Initialize prompt template
        
        Args:
            template: Template string với placeholders {variable}
            required_vars: List các biến bắt buộc trong template
        """
        self.template = template
        self.required_vars = required_vars or []
    
    def validate_variables(self, variables: Dict[str, Any]) -> None:
        """
        Validate xem có đủ các biến required không
        
        Args:
            variables: Dict các biến để fill vào template
            
        Raises:
            ValueError: Nếu thiếu required variables
        """
        missing_vars = [var for var in self.required_vars if var not in variables]
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
    
    def format(self, **kwargs) -> str:
        """
        Format template với variables
        
        Args:
            **kwargs: Các biến để fill vào template
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: Nếu thiếu required variables
        """
        self.validate_variables(kwargs)
        return self.template.format(**kwargs)
    
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """
        Get default parameters cho LLM (temperature, max_tokens, etc.)
        
        Returns:
            Dict chứa default params
        """
        pass


class PromptTemplate(BasePromptTemplate):
    """
    Concrete implementation của prompt template
    """
    
    def __init__(
        self, 
        template: str, 
        required_vars: list[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 10000,
        system_prompt: Optional[str] = None
    ):
        super().__init__(template, required_vars)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
    
    def get_default_params(self) -> Dict[str, Any]:
        """Get default LLM parameters"""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def get_system_prompt(self) -> Optional[str]:
        """Get system prompt nếu có"""
        return self.system_prompt