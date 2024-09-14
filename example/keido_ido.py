from fastapi import FastAPI, WebSocket

app = FastAPI()

r = Redis()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # data には 相手のuser_id と 自分の座標
        data = await websocket.receive_text()

        # 自分の緯度・経度を登録
        user_id = data["user_id"]
        loc = {
            "ido": data["ido"],
            "keido": data["keido"],
        }
        r.json().set(user_id, "$", loc)

        # 相手の経度・緯度を取得
        other_user_id = data["other_user_id"]
        others_keido_ido = r.json().get(other_user_id, "$")

        await websocket.send_text(f"data: {others_keido_ido}")
