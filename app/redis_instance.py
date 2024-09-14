from redis import Redis
from datetime import timedelta

matched_pair_redis: Redis = Redis(
    host="localhost", port=6379, db=0, decode_responses=True
)


class MatchedPair:
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
        pair: str = self.r.get(user_id)
        self.r.delete(user_id)
        self.r.delete(pair)


matched_pair = MatchedPair(matched_pair_redis)


finding_match_redis: Redis = Redis(
    host="localhost", port=6379, db=1, decode_responses=True
)

playing_data_redis: Redis = Redis(
    host="localhost", port=6379, db=2, decode_responses=True
)


class PlayingData:
    # divider
    D: str = ","

    def __init__(self, redis: Redis) -> None:
        self.r = redis

    def set(self, user_id: str, longitude: float, latitude: float) -> None:
        key = user_id
        value = f"{longitude}{self.D}{latitude}"
        self.r.set(key, value, ex=timedelta(minutes=1))

    def get(self, user_id: str) -> (float, float, bool):
        value: str | None = self.r.get(user_id)
        if not value:
            return (0, 0, False)
        values: list[str] = value.split(self.D)
        longitude: float = float(values[0])
        latitude: float = float(values[1])
        return (longitude, latitude, True)


playing_data = PlayingData(playing_data_redis)
