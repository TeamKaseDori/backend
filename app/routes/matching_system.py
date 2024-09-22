import asyncio
import random
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket, status

from app.redis_instance import find_match, matched_pair

# 1. listen matche
# 2. start DataGateway.run()
# 3. find match


# 他の人が自分をマッチしたことを聞く
class MatchSuccessNotifier:
    def __init__(
        self,
        match_success_checker: Callable[[], dict[str, Any] | None],
        on_close: Callable[[], Awaitable[None]],
    ) -> None:
        # Redis PubSub の関数を使う
        self.match_success_checker = match_success_checker
        self.on_close = on_close

    async def run(self, listener: Callable[[str], None]) -> None:
        while True:
            print("in match success notifier")
            await asyncio.sleep(0.5)

            # test
            await asyncio.sleep(8)
            print("8.5s")

            message = self.match_success_checker()
            if message is not None:
                listener(message["user_id"])
                return

    async def close(self):
        await self.on_close()


# websocket のデータを処理
class DataGateway:
    def __init__(
        self,
        websocket: WebSocket,
        does_abort: Callable[[Any], bool],
    ):
        self._websocket = websocket
        self._does_abort = does_abort

    async def run(
        self,
        notify_coming_data: Callable[[Any], None],
        notify_abort: Callable[[], None],
    ) -> None:
        while True:
            print("in DataGateway")
            data: dict = await self._websocket.recieve_json()
            if self._does_abort(data):
                notify_abort()
                break

            notify_coming_data(data)

    async def send_json(self, data: dict):
        await self._websocket.send_json(data)

    async def close(self) -> None:
        await self._websocket.close(status.WS_1000_NORMAL_CLOSURE)


# マッチングをする
class MatchService:
    _user_data_id: str = "user_data_id"

    def __init__(
        self, user_id: str, match_radius_m_min: float, match_radius_m_max: float
    ) -> None:
        self.user_id: str = user_id
        self._match_radius_m_min: float = match_radius_m_min
        self._match_radius_m_max: float = match_radius_m_max

        self._aborted: bool = False
        self._match_success_by_the_other: bool = False
        self.pair_user_id: str | None = None

        self._user_data: str | None = None
        self._applied_user_data_id: str | None = None

    async def run(
        self,
        on_success: Callable[[str], Awaitable[None]],
        on_abort: Callable[[], Awaitable[None]],
    ) -> str | None:
        print("enter matchservice.run")
        await self.websocket.accept()
        while True:
            await asyncio.sleep(0.5)

            if self._aborted:
                self._abort()
                await on_abort()
                return None

            self._apply_user_data()

            # listen match
            if self._match_success_by_the_other:
                self._success()
                await on_success(self.pair_user_id)
                return self.pair_user_id

            # search match
            match_success: bool = self._find_match()
            if match_success:
                self._success()
                on_success(self.pair_user_id)
                return self.pair_user_id

    def _apply_user_data(self) -> None:
        if self._user_data is None:
            return
        if self._user_data[self._user_data_id] == self._applied_user_data_id:
            return

        # 座標redisに送る
        find_match.add(
            self.user_id, self._user_data["longitude"], self._user_data["latitude"]
        )
        print(f"send data: {self._user_data}")

        self._applied_user_data_id = self._user_data[self._user_data_id]  # type: ignore

    def _find_match(self) -> bool:
        # find pair user
        if self._user_data is None:
            return False

        candidates = find_match.find(
            self.user_id, self._match_radius_m_min, self._match_radius_m_max
        )
        if not candidates:
            return False

        random_index: int = random.randint(0, len(candidates) - 1)
        pair_candidate_id: str = candidates[random_index]

        ok = find_match.pop(self.user_id, pair_candidate_id)
        if not ok:
            return False
        pair_user_id = pair_candidate_id

        # redis pub/sub で相手に伝える
        find_match.publish(pair_user_id)

        # マッチredis へ登録
        matched_pair.add(self.user_id, pair_user_id)

        return True

    def _success(self) -> None:
        print(f"in success: {self.pair_user_id}")

    def _abort(self) -> None:
        # 緯度経度dbから削除
        find_match.danger_delete(self.user_id)
        # マッチdbから削除
        matched_pair.delete(self.user_id)
        print("abort from match service")

    def listen_user_data(self, data: dict) -> None:
        self._user_data = data
        self._user_data[self._user_data_id] = uuid.uuid4()
        print(f"notified: {data}")

    def listen_match_success_by_the_other(self, other_user_id: str) -> None:
        self._match_success_by_the_other = True
        self.pair_user_id = other_user_id

    def listen_abort(self) -> None:
        self._aborted = True
