import uuid

from fastapi import APIRouter

from app.token import new_token

router = APIRouter()


@router.get("/register")
def register() -> dict:
    user_id: str = str(uuid.uuid4())
    token: str = new_token(user_id)
    return {"token": token}
