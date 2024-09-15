from fastapi import APIRouter, WebSocket, Depends
from fastapi.security import OAuth2PasswordBearer
from .redis_instance import playing_data
import json

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    # 実際の認証ロジックをここに実装します
    # ここでは仮にトークンがユーザーIDとして扱われると仮定します
    user_id = token
    return user_id


@router.websocket("/playing")
async def playing(websocket: WebSocket, user_id: str = Depends(get_current_user)) -> None:
    await websocket.accept()  # WebSocket接続の受け入れ

    while True:
        try:
            # クライアントから緯度経度のJSONを受信
            data = await websocket.receive_text()
            message = json.loads(data)

            # 緯度と経度を取得
            latitude = message.get("latitude")
            longitude = message.get("longitude")

            # 緯度と経度が正しく取得できた場合の処理
            if latitude is not None and longitude is not None:
                # Redisに緯度と経度を保存
                playing_data.set(user_id, longitude, latitude)

                # Redisから相手のデータを取得
                other_longitude, other_latitude, data_exists = playing_data.get(user_id)

                if data_exists:
                    # クライアントに緯度と経度を送信
                    response_data = {
                        "longitude": other_longitude,
                        "latitude": other_latitude
                    }
                    await websocket.send_json(response_data)
                else:
                    # データが存在しない場合のエラーメッセージ
                    await websocket.send_text("相手のデータが存在しません。")
            else:
                await websocket.send_text("データ型が正しくありません。")

        except Exception as e:
            # エラーが発生した場合の処理
            await websocket.send_text(f"An error occurred: {str(e)}")
            break

    # WebSocket接続の終了
    await websocket.close()
