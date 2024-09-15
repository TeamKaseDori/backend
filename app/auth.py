import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

USER_ID = "user_id"


class TokenData(BaseModel):
    user_id: str


def get_user_info(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    token = credentials.credentials
    try:
        claimes = jwt.decode(
            token, SECRET_KEY, algorithms=ALGORITHM, requires=["exp", USER_ID]
        )
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token_data = TokenData(user_id=claimes[USER_ID])
    return token_data


@router.get("/register")
def register() -> dict:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    user_id: str = str(uuid.uuid4())
    claimes: dict[str, Any] = {
        "exp": expire,
        USER_ID: user_id,
    }
    token = jwt.encode(claimes, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token}
