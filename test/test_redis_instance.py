import math

import pytest

from app.redis_instance import FindMatchRepo, MatchedPairRepo, PlayDataRepo


@pytest.fixture
def redis():
    import fakeredis

    redis_client = fakeredis.FakeRedis(decode_responses=True)
    return redis_client


def test_matched_pair_class(redis) -> None:
    matched_pair = MatchedPairRepo(redis)

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


def test_find_match_class(redis):
    find_match = FindMatchRepo(redis)
    # min~max の範囲から取得できているか
    find_match.add("far", 50, 50)
    find_match.add("mid", -52, -55)
    find_match.add("center", -50, -50)
    candidates = find_match.find("center", 10000000, 1000000000)
    assert candidates == ["far"]

    # 正しく追加できてるか
    find_match.add("user", 0, 0)
    (x, y), *_ = redis.geopos(FindMatchRepo.KEY, "user")
    assert math.isclose(x, 0, abs_tol=1e-4) is True
    assert math.isclose(y, 0, abs_tol=1e-4) is True

    # add で更新もできてるか
    find_match.add("user", 10, 10)
    (x, y), *_ = redis.geopos(FindMatchRepo.KEY, "user")
    assert math.isclose(x, 0, abs_tol=1e-4) is False
    assert math.isclose(y, 0, abs_tol=1e-4) is False

    # pop で消えるか
    find_match.add("user2", 20, 10)
    find_match.pop("user", "user2")
    res = redis.geopos(FindMatchRepo.KEY, "user", "user2")
    assert res == [None, None]

    # pop 実行後10秒はロックされたまま
    find_match.add("locked_user1", 0, 10)
    find_match.add("locked_user2", 10, 0)
    find_match.pop("locked_user1", "locked_user2")
    find_match.add("locked_user1", 0, 10)
    find_match.add("locked_user2", 10, 0)
    res = redis.geopos(FindMatchRepo.KEY, "locked_user1", "locked_user2")
    assert res == [None, None]

    find_match.add("user1", 0, 0)
    find_match.add("user2", 10, 0)
    find_match.add("user3", 20, 0)
    find_match.pop("user1", "user2")
    find_match.pop("user2", "user3")
    user2_res, user3_res = redis.geopos(FindMatchRepo.KEY, "user2", "user3")
    assert user2_res is None
    assert user3_res is not None
    # user2 は locked, user3 は locked でない
    # そのため、user3 は即操作可能になる
    find_match.add("user2", -10, -20)
    find_match.add("user3", -10, -10)
    user2_res, user3_res = redis.geopos(FindMatchRepo.KEY, "user2", "user3")
    assert user2_res is None
    assert math.isclose(user3_res[0], -10, abs_tol=1e-4)
    assert math.isclose(user3_res[1], -10, abs_tol=1e-4)


def test_playing_data_class(redis) -> None:
    playing_data = PlayDataRepo(redis)

    user_id: str = "user_id"
    longitude: float = 1.2
    latitude: float = 3.5
    playing_data.set(user_id, longitude, latitude)
    res_longitude, res_latitude, res_ok = playing_data.get(user_id)

    assert res_ok is True
    assert res_longitude == longitude
    assert res_latitude == latitude
