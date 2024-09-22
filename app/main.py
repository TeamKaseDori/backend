from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, matching, playing

app: FastAPI = FastAPI()
app.include_router(auth.router)
app.include_router(matching.router)
app.include_router(playing.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/welcome")
async def welcome() -> dict:
    return {"message": "welcome"}
