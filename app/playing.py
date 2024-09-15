from fastapi import APIRouter, WebSocket
from .redis_instance import playing_data_redis
import json

router = APIRouter()


@router.websocket("/playing")
async def playing(websocket: WebSocket) -> None:
    await websocket.accept()  # WebSocket接続の受け入れ

    while True:
        try:
            # クライアントからメッセージを受け取る
            data = await websocket.receive_text()

            message = json.loads(data)

            # 緯度と経度を取得
            latitude = message.get("latitude")
            longitude = message.get("longitude")

            if latitude is not None and longitude is not None:
                # Redisに緯度と経度を保存
                playing_data_redis.set("latitude", latitude)
                playing_data_redis.set("longitude", longitude)

                # クライアントに緯度と経度を送信
                data = {"latitude": latitude, "longitude": longitude}
                await websocket.send_json(data)
        except Exception as e:
            # エラーが発生した場合の処理
            await websocket.send_text(f"An error occurred: {str(e)}")
            break

    # WebSocket接続の終了
    await websocket.close()



@router.get("/item")
async def fname() -> dict:
    playing_data_redis.set("a", "b")
    return {"message": playing_data_redis.get("a")}
