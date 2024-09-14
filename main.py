from fastapi import FastAPI
from redis import Redis

app = FastAPI()
matched_pair_redis: Redis = Redis(
    host="localhost", port=6379, db=0, decode_responses=True
)
finding_match_redis: Redis = Redis(
    host="localhost", port=6379, db=1, decode_responses=True
)
playing_data_redis: Redis = Redis(
    host="localhost", port=6379, db=2, decode_responses=True
)


@app.get("/welcome")
async def welcome() -> dict:
    return {"message": "welcome"}
