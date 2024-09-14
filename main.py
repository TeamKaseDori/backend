from fastapi import FastAPI

from app import auth, matching, playing

app: FastAPI = FastAPI()
app.include_router(auth.router)
app.include_router(matching.router)
app.include_router(playing.router)


@app.get("/welcome")
async def welcome() -> dict:
    return {"message": "welcome"}
