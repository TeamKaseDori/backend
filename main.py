from fastapi import FastAPI

from app import auth, matching, playing
from redis import Redis

app: FastAPI = FastAPI()
app.include_router(auth.router)
app.include_router(matching.router)
app.include_router(playing.router)

HOST = "red-crj4ijij1k6c73fjhnsg"

r: Redis = Redis(host=HOST, port=6379, db=8, decode_responses=True)
r.set("a", "hello")


@app.get("/welcome")
async def welcome() -> dict:
    return {"message": r.get("a")}
