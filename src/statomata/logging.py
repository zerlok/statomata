import logging
import typing as t

from typing_extensions import override

from statomata.abc import StateMachineAsyncSubscriber, StateMachineSubscriber


class LoggingSubscriber(StateMachineSubscriber[object, object, object]):
    def __init__(self, log: t.Optional[logging.Logger] = None) -> None:
        self.__log = log or logging.getLogger(__name__)

    @override
    def notify_started(self, state: object) -> None:
        self.__log.info("started from %s", state)

    @override
    def notify_state_entered(self, state: object, income: object) -> None:
        self.__log.info("entered %s", state)

    @override
    def notify_state_outcome(self, state: object, income: object, outcome: object) -> None:
        self.__log.info("outcome %s", state)

    @override
    def notify_state_left(self, state: object, income: object) -> None:
        self.__log.info("left %s", state)

    @override
    def notify_state_failed(self, state: object, error: Exception) -> None:
        self.__log.info("failed %s", state)

    @override
    def notify_transitioned(self, source: object, dest: object) -> None:
        self.__log.info("transitioned from %s to %s", source, dest)

    @override
    def notify_finished(self, state: object) -> None:
        self.__log.info("finished at %s", state)


class AsyncLoggingSubscriber(StateMachineAsyncSubscriber[object, object, object]):
    def __init__(self, log: t.Optional[logging.Logger] = None) -> None:
        self.__log = log or logging.getLogger(__name__)

    @override
    async def notify_started(self, state: object) -> None:
        self.__log.info("started from %s", state)

    @override
    async def notify_state_entered(self, state: object, income: object) -> None:
        self.__log.info("entered %s", state)

    @override
    async def notify_state_outcome(self, state: object, income: object, outcome: object) -> None:
        self.__log.info("outcome %s", state)

    @override
    async def notify_state_left(self, state: object, income: object) -> None:
        self.__log.info("left %s", state)

    @override
    async def notify_state_failed(self, state: object, error: Exception) -> None:
        self.__log.info("failed %s", state)

    @override
    async def notify_transitioned(self, source: object, dest: object) -> None:
        self.__log.info("transitioned from %s to %s", source, dest)

    @override
    async def notify_finished(self, state: object) -> None:
        self.__log.info("finished at %s", state)
