from .redis_instance import MatchedPair, PlayingData


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def set(self, key: str, value: str, *args, **kargs) -> None:
        self.store[key] = value

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def delete(self, key: str) -> None:
        del self.store[key]


def test_matched_pair_class() -> None:
    redis = FakeRedis()
    matched_pair = MatchedPair(redis)

    user_id1: str = "userid1"
    user_id2: str = "userid2"

    matched_pair.add(user_id1, user_id2)
    assert matched_pair.get(user_id1) == user_id2
    assert matched_pair.get(user_id2) == user_id1

    matched_pair.delete(user_id1)
    assert matched_pair.get(user_id1) is None
    assert matched_pair.get(user_id2) is None

    matched_pair.add(user_id1, user_id2)
    matched_pair.delete(user_id2)
    assert matched_pair.get(user_id1) is None
    assert matched_pair.get(user_id2) is None


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
