from fastapi import APIRouter

from app.redis_instance import playing_data_redis

router = APIRouter()


@router.websocket("/playing")
async def playing() -> None:
    playing_data_redis.set("a", "b")
    pass
