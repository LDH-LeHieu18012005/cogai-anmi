from fastapi import APIRouter, HTTPException
from app.models.prompts import (
    PromptTemplateListRequest,
    PromptFormatRequest,
    CustomTemplateRequest,
    PromptExecuteRequest
)
from app.models.responses import ChatResponse, ErrorResponse
from app.services.prompt_service import prompt_service
from app.utils.errors import AIException

router = APIRouter()

@router.get(
    "/templates",
    summary="List prompt templates",
    description="Lấy danh sách tất cả prompt templates có sẵn"
)
async def list_templates(category: str = None):
    """
    List tất cả prompt templates hoặc filter theo category
    
    - **category**: Filter theo category (chat, summarization, extraction) - optional
    """
    try:
        result = prompt_service.list_templates(category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/templates/{template_name}",
    summary="Get template info",
    description="Lấy chi tiết của một prompt template"
)
async def get_template(template_name: str):
    """
    Get chi tiết của một template
    
    - **template_name**: Tên của template (vd: chat.general)
    """
    try:
        result = prompt_service.get_template_info(template_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/templates/format",
    summary="Format prompt template",
    description="Format một prompt template với variables"
)
async def format_template(request: PromptFormatRequest):
    """
    Format một prompt template với variables
    
    Trả về formatted prompt, system prompt và default params
    """
    try:
        result = prompt_service.format_template(
            template_name=request.template_name,
            variables=request.variables,
            override_temperature=request.override_temperature,
            override_max_tokens=request.override_max_tokens
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/templates/custom",
    summary="Create custom template",
    description="Tạo một custom prompt template"
)
async def create_custom_template(request: CustomTemplateRequest):
    """
    Tạo một custom prompt template
    
    Template name phải bắt đầu với 'custom.'
    """
    try:
        result = prompt_service.create_custom_template(
            template_name=request.template_name,
            template=request.template,
            required_vars=request.required_vars,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/templates/execute",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Execute prompt template",
    description="Format template và execute với LLM trong một request"
)
async def execute_template(request: PromptExecuteRequest):
    """
    Format template và execute với LLM
    
    Đây là shortcut để format + call LLM trong một request.
    Nếu bạn chỉ muốn format, dùng /templates/format
    """
    try:
        response = await prompt_service.execute_template(
            template_name=request.template_name,
            variables=request.variables,
            provider_name=request.provider.value,
            model=request.model,
            override_temperature=request.override_temperature,
            override_max_tokens=request.override_max_tokens
        )
        return response
    except AIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))