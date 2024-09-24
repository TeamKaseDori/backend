import asyncio
import random
from asyncio.exceptions import CancelledError
from collections.abc import Callable
from typing import Any

import redis.client
from fastapi import WebSocket, status
from pydantic import BaseModel

from app.redis_instance import FindMatchRepo, MatchedPairRepo

# 1. listen matche
# 2. start DataGateway.run()
# 3. find match


# 他の人が自分をマッチしたことを聞く
class MatchSuccessNotifier:
    def __init__(
        self,
        user_id: str,
        redis_pub_sub: redis.client.PubSub,
    ) -> None:
        self._user_id: str = user_id
        self._pub_sub: redis.client.PubSub = redis_pub_sub
        self._listeners: list[Callable[[str], None]] = []
        self._task: asyncio.Task | None = None

    def add_listener(self, f: Callable[[str], None]) -> None:
        self._listeners.append(f)

    def init(self) -> None:
        self._pub_sub.subscribe(self._user_id)

    def start(self, on_exception: Callable[[], None]) -> None:
        def on_close() -> None:
            self._pub_sub.unsubscribe(self._user_id)

        self._task = asyncio.create_task(self._execute(on_close, on_exception))

    async def _execute(
        self, on_close: Callable, on_exception: Callable[[], None]
    ) -> None:
        print("in match success notifier")
        try:
            while True:
                await asyncio.sleep(0.5)

                message = self._pub_sub.get_message()
                if message is not None and message["type"] == "message":
                    for f in self._listeners:
                        f(message["data"])
                    return
        # 子スレッドの例外は親スレッドへ伝達されない
        # そのため、ここが最上位
        except:  # noqa: E722
            on_exception()
        finally:
            on_close()

    def stop(self):
        if self._task is not None:
            self._task.cancel()

    def abnormal_stop(self):
        self.stop()


# websocket のデータを処理
class DataGateway:
    def __init__(
        self,
        websocket: WebSocket,
    ):
        self._websocket = websocket
        self._aobrt_listeners: list[Callable[[], None]] = []
        self._update_listeners: list[Callable[[UserData], None]] = []
        self._task: asyncio.Task | None = None
        self._sending_message: dict[str, Any] | None = None

    def add_abort_listener(self, f: Callable[[], None]) -> None:
        self._aobrt_listeners.append(f)

    def add_update_listener(self, f: Callable[["UserData"], None]) -> None:
        self._update_listeners.append(f)

    def add_sending_message(self, message: dict[str, Any]) -> bool:
        if self._sending_message is not None:
            return False
        self._sending_message = message
        return True

    def start(self, on_exception: Callable[[], None]) -> None:
        self._task = asyncio.create_task(self._excute(on_exception))

    async def _excute(self, on_exception: Callable[[], None]) -> None:
        await self._websocket.accept()
        try:
            print("start websocket")
            while True:
                print("waiting for receive")
                json_data: dict = await self._websocket.receive_json()
                print("----------------received: ", json_data)
                user_sending_data: UserSendingData = UserSendingData(**json_data)
                print("------------validate done")
                if user_sending_data.abort is True:
                    for f in self._aobrt_listeners:
                        f()
                    break

                for f in self._update_listeners:
                    f(UserData(**user_sending_data.model_dump()))

                await self._websocket.send_json(self._sending_message)
                self._sending_message = None

        except CancelledError as e:
            if e is not None and "abnormal" in e.args:
                for f in self._aobrt_listeners:
                    f()
                await self._websocket.close(status.WS_1011_INTERNAL_ERROR)
            await self._websocket.close(status.WS_1000_NORMAL_CLOSURE)

        # WebSocketDisconnect など
        except:  # noqa: E722
            print("!!!!!!!!!!!!!exception in DataGateway")
            for f in self._aobrt_listeners:
                f()
            await self._websocket.close(status.WS_1011_INTERNAL_ERROR)
            on_exception()

        else:
            await self._websocket.close(status.WS_1000_NORMAL_CLOSURE)

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

    def abnormal_stop(self) -> None:
        if self._task is not None:
            self._task.cancel("abnormal")


# マッチングをする
class MatchService:
    def __init__(
        self,
        user_id: str,
        match_radius_m_min: float,
        match_radius_m_max: float,
        data_gateway: DataGateway,
        match_success_notifier: MatchSuccessNotifier,
        find_match_repo: FindMatchRepo,
        matched_pair_repo: MatchedPairRepo,
    ) -> None:
        self.user_id: str = user_id
        self._match_radius_m_min: float = match_radius_m_min
        self._match_radius_m_max: float = match_radius_m_max

        self._user_data: UserData | None = None
        self._aborted: bool = False
        self._match_success_by_the_other: bool = False
        self.pair_user_id: str | None = None

        self._data_gateway: DataGateway = data_gateway
        self._match_success_notifier: MatchSuccessNotifier = match_success_notifier
        self._find_match_repo: FindMatchRepo = find_match_repo
        self._matched_pair_repo: MatchedPairRepo = matched_pair_repo

    async def run(self) -> None:
        self._data_gateway.add_abort_listener(self.listen_abort)
        self._data_gateway.add_update_listener(self.listen_user_data_update)
        self._match_success_notifier.add_listener(
            self.listen_match_success_by_the_other
        )

        self._match_success_notifier.init()

        def on_exception() -> None:
            self._data_gateway.abnormal_stop()
            self._match_success_notifier.abnormal_stop()

        match_service_task = asyncio.create_task(self._run())
        self._data_gateway.start(on_exception)
        self._match_success_notifier.start(on_exception)
        await match_service_task

        print("will stop all dependencies")
        self._data_gateway.stop()
        self._match_success_notifier.stop()
        print("all dependencies were stopped")

    async def _run(self) -> None:
        print("enter matchservice.run")
        try:
            while True:
                await asyncio.sleep(0.5)

                if self._aborted:
                    self._abort()
                    return None

                self._apply_user_data()

                # listen match
                if self._match_success_by_the_other:
                    self._success()

                # search match
                match_success: bool = self._find_match()
                if match_success:
                    self._success()
        except:  # noqa: E722
            self._abort()

    def _apply_user_data(self) -> None:
        if self._user_data is None:
            return
        if self._user_data._is_applied:
            return

        # 座標redisに送る
        self._find_match_repo.add(
            self.user_id, self._user_data.longitude, self._user_data.latitude
        )
        self._user_data._is_applied = True
        print(f"send data: {self._user_data}")

    def _find_match(self) -> bool:
        # find pair user
        if self._user_data is None:
            return False

        candidates = self._find_match_repo.find(
            self.user_id, self._match_radius_m_min, self._match_radius_m_max
        )
        if not candidates:
            return False

        random_index: int = random.randint(0, len(candidates) - 1)
        pair_candidate_id: str = candidates[random_index]

        ok = self._find_match_repo.pop(self.user_id, pair_candidate_id)
        if not ok:
            return False
        pair_user_id = pair_candidate_id

        # redis pub/sub で相手に伝える
        self._find_match_repo.publish(pair_user_id, self.user_id)

        # マッチredis へ登録
        self._matched_pair_repo.add(self.user_id, pair_user_id)

        return True

    def _success(self) -> None:
        print(f"in success: {self.pair_user_id}")
        assert self.pair_user_id is not None
        message = MatchSuccessData(paire_user_id=self.pair_user_id).model_dump()  # pyright: ignore
        self._data_gateway.add_sending_message(message)

    def _abort(self) -> None:
        # 緯度経度dbから削除
        self._find_match_repo.danger_delete(self.user_id)
        # マッチdbから削除
        self._matched_pair_repo.delete(self.user_id)
        print("abort from match service")

    def listen_user_data_update(self, data: "UserData") -> None:
        self._user_data = data
        print(f"notified: {data}")

    def listen_match_success_by_the_other(self, other_user_id: str) -> None:
        self._match_success_by_the_other = True
        self.pair_user_id = other_user_id

    def listen_abort(self) -> None:
        self._aborted = True


class UserData(BaseModel):
    _is_applied: bool = False
    latitude: float  # 緯度
    longitude: float  # 経度


class UserSendingData(UserData):
    abort: bool


class MatchSuccessData(BaseModel):
    paire_user_id: str
