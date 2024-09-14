from main import app


@app.websocket("/playing")
async def playing() -> None:
    pass
