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

```json
{ "token": token }
```

## `websocket /matching`

### リクエスト

クエリー（必須）: `/matching?token=<TOKEN>`
クエリー（オプション）: `/matching?min=400&max=1000` のように `min` と `max` でマッチング範囲を変更できます

### WebSocket

```json
{ "abort": boolean, "longitude": float, "latitude": float }
```

↑のデータを数秒おき（適当でいい）に送ってください `abort` はマッチングの中止です（ `true` が中止） 

マッチングが完了したら

```json
{"pair_user_id": pair_user_id}
```

が帰ってきます

## `websocket /playing`

### リクエスト

クエリー（必須）: `/matching?token=<TOKEN>`

### レスポンス

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
