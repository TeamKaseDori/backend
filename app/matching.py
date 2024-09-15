import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket

from .auth import TokenData, get_user_info
from .matching_system import DataGateway, MatchService, MatchSuccessNotifier
from .redis_instance import find_match

router = APIRouter()


@router.websocket("/matching")
async def matching(
    websocket: WebSocket, token_data: Annotated[TokenData, Depends(get_user_info)]
):
    user_id: str = token_data.user_id

    find_match.subscribe(user_id)

    async def on_close() -> None:
        find_match.unsubscribe(user_id)

    match_service: MatchService = MatchService(user_id)
    match_success_notifier: MatchSuccessNotifier = MatchSuccessNotifier(
        find_match.get_message, on_close
    )
    gateway: DataGateway = DataGateway(websocket, lambda data: data.get("abort"))

    async def on_success(pair_user_id: str) -> None:
        await match_success_notifier.close()
        await gateway.send_json({"pair_user_id": pair_user_id})
        await gateway.close()

    async def on_abort() -> None:
        await match_success_notifier.close()
        await gateway.close()

    task1 = asyncio.create_task(
        match_success_notifier.run(match_service.notify_match_success_by_the_other)
    )
    task2 = asyncio.create_task(
        gateway.run(match_service.notify_match_info, match_service.notify_abort)
    )
    task3 = asyncio.create_task(match_service.run(on_success, on_abort))
    await asyncio.wait([task3])
    task1.cancel()
    task2.cancel()
