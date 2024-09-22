import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import Claimes, new_token, verify_token

router = APIRouter()
security = HTTPBearer()


def get_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    token: str = credentials.credentials
    try:
        claimes: Claimes = verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="トークンが不正です"
        )
    return claimes.user_id


def get_user_id_from_query(token: Annotated[str, Query()]) -> str:
    try:
        claimes: Claimes = verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="トークンが不正です"
        )
    return claimes.user_id


@router.get("/register")
def register() -> dict:
    user_id: str = str(uuid.uuid4())
    token: str = new_token(user_id)
    return {"token": token}
