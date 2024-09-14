from .redis_instance import PlayingData


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self.store[key] = value

    def get(self, key: str) -> str | None:
        return self.store.get(key)


def test_playing_data_class() -> None:
    redis = FakeRedis()
    playing_data = PlayingData(redis)

    user_id: str = "user_id"
    longitude: float = 1.2
    latitude: float = 3.5
    playing_data.set(user_id, longitude, latitude)
    res_longitude, res_latitude, res_ok = playing_data.get(user_id)

    assert res_ok is True
    assert res_longitude == longitude
    assert res_latitude == latitude
