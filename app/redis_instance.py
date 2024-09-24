from datetime import timedelta

from redis import Redis
from redis.connection import ConnectionPool
from redis.exceptions import ResponseError

from .load_env import REDIS_HOST

_matched_pair_redis_pool: ConnectionPool = ConnectionPool(
    host=REDIS_HOST, port=6379, db=0, decode_responses=True
)
_find_match_redis_pool: ConnectionPool = ConnectionPool(
    host=REDIS_HOST, port=6379, db=1, decode_responses=True, protocol=3
)
_play_data_redis_pool: ConnectionPool = ConnectionPool(
    host=REDIS_HOST, port=6379, db=2, decode_responses=True
)


def get_matched_pair_repo() -> "MatchedPairRepo":
    r = Redis.from_pool(_matched_pair_redis_pool)
    return MatchedPairRepo(r)


def get_find_match_repo() -> "FindMatchRepo":
    r = Redis.from_pool(_find_match_redis_pool)
    return FindMatchRepo(r)


def get_play_data_repo() -> "PlayDataRepo":
    r = Redis.from_pool(_play_data_redis_pool)
    return PlayDataRepo(r)


class MatchedPairRepo:
    ex: timedelta = timedelta(hours=6)

    def __init__(self, redis: Redis) -> None:
        self.r = redis

    def add(self, user_id1: str, user_id2: str) -> None:
        self.r.set(user_id1, user_id2, ex=self.ex)
        self.r.set(user_id2, user_id1, ex=self.ex)

    def get(self, user_id: str) -> str | None:
        pair: str | None = self.r.get(user_id)
        return pair

    def delete(self, user_id: str) -> None:
        pair: str | None = self.r.get(user_id)
        if pair is None:
            return
        self.r.delete(user_id)
        self.r.delete(pair)


class FindMatchRepo:
    KEY: str = "user_coordinate"
    EX_LOCK: timedelta = timedelta(seconds=10)

    def __init__(self, redis: Redis) -> None:
        self.r = redis
        self.pub_sub = redis.pubsub()

    def _perform_lock(self, user_id: str) -> bool:
        return self.r.set(user_id, 1, nx=True, ex=self.EX_LOCK)

    def _perform_lock_2(self, user_id1: str, user_id2: str) -> bool:
        can_update1: bool = self._perform_lock(user_id1)
        can_update2: bool = self._perform_lock(user_id2)
        if can_update1 and can_update2:
            return True

        if can_update1:
            self._unlock(user_id1)
        if can_update2:
            self._unlock(user_id2)
        return False

    def _unlock(self, user_id: str) -> None:
        self.r.delete(user_id)

    def add(self, user_id: str, longitude: float, latitude: float) -> None:
        # ロック中は更新しない
        can_update: bool = self._perform_lock(user_id)
        if not can_update:
            return

        self.r.geoadd(
            self.KEY,
            [longitude, latitude, user_id],
        )

        # 更新した後にすぐに探せる状態にしたいため
        self._unlock(user_id)

    def pop(self, user_id, pair_user_id) -> bool:
        # ロック中は更新しない
        # ロックの解除はしない、マッチ成立を伝えている間に追加されたくないため
        can_update: bool = self._perform_lock_2(user_id, pair_user_id)
        if not can_update:
            return False

        self.r.zrem(self.KEY, user_id, pair_user_id)
        return True

    # abort 専用
    def danger_delete(self, user_id) -> None:
        self.r.zrem(self.KEY, user_id)

    def find(self, user_id: str, min_m: float, max_m: float) -> list[str]:
        # user_id が登録されていない可能性がある
        try:
            max_range = self.r.geosearch(
                self.KEY, member=user_id, radius=max_m, unit="m"
            )
            min_range = self.r.geosearch(
                self.KEY, member=user_id, radius=min_m, unit="m"
            )
        except ResponseError:
            return []
        candidates = list(set(max_range) - set(min_range))
        return candidates

    def publish(self, pair_user_id: str, user_id: str):
        self.r.publish(pair_user_id, user_id)


class PlayDataRepo:
    # divider
    D: str = ","

    def __init__(self, redis: Redis) -> None:
        self.r = redis

    def set(self, user_id: str, longitude: float, latitude: float) -> None:
        key = user_id
        value = f"{longitude}{self.D}{latitude}"
        self.r.set(key, value, ex=timedelta(minutes=1))

    def get(self, user_id: str) -> tuple[float, float, bool]:
        value: str | None = self.r.get(user_id)
        if not value:
            return (0, 0, False)
        values: list[str] = value.split(self.D)
        longitude: float = float(values[0])
        latitude: float = float(values[1])
        return (longitude, latitude, True)
