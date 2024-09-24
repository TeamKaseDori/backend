import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket

from app.dependencies import get_user_id_from_query
from app.redis_instance import find_match, matched_pair

from .matching_system import DataGateway, MatchService, MatchSuccessNotifier

router = APIRouter()


@router.websocket("/matching")
async def matching(
    websocket: WebSocket,
    user_id: Annotated[str, Depends(get_user_id_from_query)],
    min: Annotated[float, Query(title="matching min radius [m]", gt=100)] = 300,
    max: Annotated[float, Query(title="matching max radius [m]", gt=300)] = 500,
):
    data_gateway: DataGateway = DataGateway(websocket)
    match_success_notifier: MatchSuccessNotifier = MatchSuccessNotifier(
        user_id, find_match.pub_sub
    )
    match_service: MatchService = MatchService(
        user_id,
        min,
        max,
        data_gateway,
        match_success_notifier,
        find_match,
        matched_pair,
    )

    task = asyncio.create_task(match_service.run())
    await task
