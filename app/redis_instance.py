from redis import Redis

matched_pair_redis: Redis = Redis(
    host="localhost", port=6379, db=0, decode_responses=True
)

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
        self.r.set(key, value)

    def get(self, user_id: str) -> (float, float, bool):
        value: str | None = self.r.get(user_id)
        if not value:
            return (0, 0, False)
        values: list[str] = value.split(self.D)
        longitude: float = float(values[0])
        latitude: float = float(values[1])
        return (longitude, latitude, True)


playing_data = PlayingData(playing_data_redis)
