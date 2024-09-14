from fastapi import FastAPI

app = FastAPI()


@app.get("/welcome")
async def welcome() -> dict:
    return {"message": "welcome"}
