import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket

import app.dependencies as d
import app.redis_instance as r

from .matching_system import DataGateway, MatchService, MatchSuccessNotifier

router = APIRouter()


@router.websocket("/matching")
async def matching(
    websocket: WebSocket,
    user_id: Annotated[str, Depends(d.get_user_id_from_query)],
    find_match_repo: Annotated[r.FindMatchRepo, Depends(d.get_find_match_repo)],
    matched_pair_repo: Annotated[r.MatchedPairRepo, Depends(d.get_matched_pair_repo)],
    min: Annotated[float, Query(title="matching min radius [m]", gt=100)] = 300,
    max: Annotated[float, Query(title="matching max radius [m]", gt=300)] = 500,
):
    data_gateway: DataGateway = DataGateway(websocket)
    match_success_notifier: MatchSuccessNotifier = MatchSuccessNotifier(
        user_id, find_match_repo.pub_sub
    )
    match_service: MatchService = MatchService(
        user_id,
        min,
        max,
        data_gateway,
        match_success_notifier,
        find_match_repo,
        matched_pair_repo,
    )

    task = asyncio.create_task(match_service.run())
    await task
