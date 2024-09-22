# SAIマッチング バックエンド

## 実行方法

```shell
source .venv/bin/activate
fastapi dev app/main.py
```

or

`uv run fastapi dev app/main.py`

## `get /register`

### リクエスト

なし

### レスポンス

Bearer認証

```json
{ "token": token }
```

## `websocket /matching`

### リクエスト

ヘッダー：Bearer token `Authorization: Bearer <Token>`

クエリー：`/matching?min=400&max=1000` のように `min` と `max` でマッチング範囲を変更できます

### WebSocket

```json
{ "abort": 1 or 0, "longitude": float, "latitude": float }
```

↑のデータを数秒おき（適当でいい）に送ってください `abort` はマッチングの中止です（ `1` が中止） 

マッチングが完了したら

```json
{"pair_user_id": pair_user_id}
```

が帰ってきます

## `websocket /playing`

### リクエスト

ヘッダー：Bearer token `Authorization: Bearer <Token>`

### WebSocket

自分の経度緯度

```json
{ "longitude": float, "latitude": float }
```

↑のデータを送ってください

データが送信された後に 相手の

```json
{ "longitude": float, "latitude": float }
```

が帰ってきます
