from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.contracts import ReadyResponse

router = APIRouter(prefix='/health', tags=['health'])


@router.get('/live')
async def live() -> dict[str, str]:
    return {'status': 'ok'}


@router.get('/ready', response_model=ReadyResponse)
async def ready(settings: Annotated[Settings, Depends(get_settings)]) -> ReadyResponse:
    return ReadyResponse(
        environment=settings.environment,
        api_prefix=settings.api_v1_prefix,
        ollama_model=settings.ollama_chat_model,
    )
