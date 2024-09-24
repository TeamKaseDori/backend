from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import app.redis_instance as r
from app.token import Claimes, verify_token

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


def get_matched_pair_repo() -> r.MatchedPairRepo:
    return r.get_matched_pair_repo()


def get_find_match_repo() -> r.FindMatchRepo:
    return r.get_find_match_repo()


def get_play_data_repo() -> r.PlayDataRepo:
    return r.get_play_data_repo()
