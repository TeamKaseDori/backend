from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, ValidationError

SECRET_KEY = "secret"
ALGORITHM = "HS256"
EXPIRE_HOURS = 8


class Claimes(BaseModel):
    exp: datetime
    user_id: str


def new_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
    claimes = Claimes(exp=expire, user_id=user_id)
    token = jwt.encode(claimes.model_dump(), SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> Claimes:
    try:
        decoded = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], requires=["exp"]
        )
        claimes = Claimes.model_validate(decoded, from_attributes=True)
    except (InvalidTokenError, ValidationError):
        raise ValueError("invalid token")
    return claimes
