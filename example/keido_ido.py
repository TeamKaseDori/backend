from typing import Annotated

from fastapi import Depends, FastAPI, WebSocket, WebSocketException, status
from pydantic import BaseModel, Field, ValidationError
from redis import Redis

from app.auth import TokenData, get_user_info

app = FastAPI()


playing_data_redis: Redis = Redis(
    host="localhost", port=6379, db=10, decode_responses=True
)


class PlayData(BaseModel):
    # 経度
    longitude: float = Field(title="keido")
    # 緯度
    latitude: float = Field(title="ido")
    # 中断
    abort: bool = Field(default=False, title="abort")


# TODO: websocket を終了するときは `matched_pair_redis` から削除
@app.websocket("/playing")
async def playing(
    websocket: WebSocket, token_data: Annotated[TokenData, Depends(get_user_info)]
):
    user_id: str = token_data.user_id

    await websocket.accept()
    while True:
        # data には 相手のuser_id と 自分の座標
        data = await websocket.receive_json()
        try:
            play_data: PlayData = PlayData.model_validate(**data)
        except ValidationError:
            raise WebSocketException(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)

        # 自分の緯度・経度を登録
        playing_data_redis.set(user_id, play_data.longitude)

        # 相手の経度・緯度を取得
        # `mathed_pair_redis` から取得
        # others_keido_ido = playing_data_redis.get("a")
        other_play_data = PlayData()

        await websocket.send_json(other_play_data.model_json_schema)
