from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from app.auth import CurrentUser
from app.parsing.service import (
    ParseError,
    ParseRequest,
    ParseResponse,
    Provider,
    ProviderError,
    get_provider,
    parse_agenda,
)

router = APIRouter(prefix="/parse", tags=["parsing"])


@router.post("", response_model=ParseResponse)
async def parse_draft(
    payload: ParseRequest,
    user: CurrentUser,
    provider: Annotated[Provider, Depends(get_provider)],
) -> ParseResponse:
    try:
        return await run_in_threadpool(parse_agenda, payload, provider)
    except ParseError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(503, str(exc)) from exc
