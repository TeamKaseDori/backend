from ../main.py import app


@app.websocket("/finding")
async def finding() -> None:
    pass
