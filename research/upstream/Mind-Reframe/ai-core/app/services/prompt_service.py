from typing import Dict, Any, Optional
from app.core.prompts.manager import prompt_manager
from app.core.llm.client import llm_client
from app.models.requests import Message, MessageRole
from app.models.responses import ChatResponse, Usage
from app.utils.errors import LLMResponseError

class PromptService:
    """
    Service layer cho prompt template functionality
    """
    
    def list_templates(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List tất cả templates hoặc filter theo category
        
        Args:
            category: Category để filter (optional)
            
        Returns:
            Dict chứa templates và metadata
        """
        templates = prompt_manager.list_templates(category)
        
        # Get template details
        template_details = []
        for template_name in templates:
            template = prompt_manager.get(template_name)
            if template:
                template_details.append({
                    "name": template_name,
                    "required_vars": template.required_vars,
                    "default_params": template.get_default_params(),
                    "has_system_prompt": template.get_system_prompt() is not None
                })
        
        return {
            "total": len(templates),
            "templates": template_details
        }
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get chi tiết của một template
        
        Args:
            template_name: Tên của template
            
        Returns:
            Dict chứa template info
            
        Raises:
            ValueError: Nếu template không tồn tại
        """
        template = prompt_manager.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        return {
            "name": template_name,
            "template": template.template,
            "required_vars": template.required_vars,
            "default_params": template.get_default_params(),
            "system_prompt": template.get_system_prompt()
        }
    
    def format_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        override_temperature: Optional[float] = None,
        override_max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format một template với variables
        
        Args:
            template_name: Tên template
            variables: Variables để fill
            override_temperature: Override temperature
            override_max_tokens: Override max_tokens
            
        Returns:
            Dict chứa formatted prompt và params
        """
        prompt, default_params = prompt_manager.format_prompt(
            template_name, 
            **variables
        )
        
        # Override params nếu có
        if override_temperature is not None:
            default_params["temperature"] = override_temperature
        if override_max_tokens is not None:
            default_params["max_tokens"] = override_max_tokens
        
        # Get system prompt
        template = prompt_manager.get(template_name)
        system_prompt = template.get_system_prompt() if template else None
        
        return {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "params": default_params
        }
    
    def create_custom_template(
        self,
        template_name: str,
        template: str,
        required_vars: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Tạo custom template
        
        Args:
            template_name: Tên template
            template: Template string
            required_vars: Required variables
            temperature: Default temperature
            max_tokens: Default max_tokens
            system_prompt: System prompt
            
        Returns:
            Dict chứa confirmation message
        """
        # Validate template name format
        if not template_name.startswith("custom."):
            raise ValueError("Custom template name must start with 'custom.'")
        
        prompt_manager.create_custom_template(
            template_name=template_name,
            template=template,
            required_vars=required_vars,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        
        return {
            "message": f"Custom template '{template_name}' created successfully",
            "template_name": template_name
        }
    
    async def execute_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        provider_name: str,
        model: Optional[str] = None,
        override_temperature: Optional[float] = None,
        override_max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """
        Format template và execute với LLM
        
        Args:
            template_name: Tên template
            variables: Variables
            provider_name: Provider name
            model: Model name
            override_temperature: Override temperature
            override_max_tokens: Override max_tokens
            
        Returns:
            ChatResponse
        """
        try:
            # Format template
            formatted = self.format_template(
                template_name,
                variables,
                override_temperature,
                override_max_tokens
            )
            
            # Get provider
            from app.models.requests import LLMProvider
            provider_enum = LLMProvider(provider_name)
            provider = llm_client.get_provider(provider_enum)
            
            # Build messages
            messages = []
            if formatted["system_prompt"]:
                messages.append(
                    Message(
                        role=MessageRole.SYSTEM,
                        content=formatted["system_prompt"]
                    )
                )
            
            messages.append(
                Message(
                    role=MessageRole.USER,
                    content=formatted["prompt"]
                )
            )
            
            # Call LLM
            response_data = await provider.chat(
                messages=messages,
                model=model,
                temperature=formatted["params"]["temperature"],
                max_tokens=formatted["params"]["max_tokens"]
            )
            
            # Convert to ChatResponse
            return ChatResponse(
                id=response_data["id"],
                content=response_data["content"],
                model=response_data["model"],
                provider=response_data["provider"],
                usage=Usage(**response_data["usage"]) if response_data.get("usage") else None
            )
            
        except Exception as e:
            raise LLMResponseError(
                message=f"Failed to execute template: {str(e)}",
                detail=str(e)
            )

# Singleton instance
prompt_service = PromptService()