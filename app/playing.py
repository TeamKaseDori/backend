from fastapi import APIRouter, WebSocket
from .redis_instance import playing_data_redis

router = APIRouter()


@router.websocket("/playing")
async def playing(websocket: WebSocket) -> None:
    await websocket.accept()

    while True:
        data = await websocket.receive_text()

    playing_data_redis.set("a", "b")
    pass


@router.get("/item")
async def fname() -> dict:
    playing_data_redis.set("a", "b")
    return {"message": playing_data_redis.get("a")}
