import logging
import typing as t

from typing_extensions import override

from statomata.abc import AsyncStateMachineSubscriber, StateMachineSubscriber


class LoggingSubscriber(StateMachineSubscriber[object, object, object]):
    def __init__(self, log: t.Optional[logging.Logger] = None) -> None:
        self.__log = log or logging.getLogger(__name__)

    @override
    def notify_initial(self, state: object) -> None:
        self.__log.info("initial %s", state)

    @override
    def notify_state_entered(self, state: object, income: object) -> None:
        self.__log.info("entered %s %s", state, income)

    @override
    def notify_income_deferred(self, state: object, income: object) -> None:
        self.__log.info("deferred %s %s", state, income)

    @override
    def notify_income_recalled(self, state: object, income: object) -> None:
        self.__log.info("recalled %s %s", state, income)

    @override
    def notify_state_outcome(self, state: object, income: object, outcome: object) -> None:
        self.__log.info("outcome %s %s %s", state, income, outcome)

    @override
    def notify_state_left(self, state: object, income: object) -> None:
        self.__log.info("left %s %s", state, income)

    @override
    def notify_state_failed(self, state: object, error: Exception) -> None:
        self.__log.warning("failed %s", state, exc_info=error)

    @override
    def notify_transition(self, source: object, destination: object) -> None:
        self.__log.info("transitioned from %s to %s", source, destination)

    @override
    def notify_final(self, state: object) -> None:
        self.__log.info("final %s", state)


class AsyncLoggingSubscriber(AsyncStateMachineSubscriber[object, object, object]):
    def __init__(self, log: t.Optional[logging.Logger] = None) -> None:
        self.__log = log or logging.getLogger(__name__)

    @override
    async def notify_initial(self, state: object) -> None:
        self.__log.info("initial %s", state)

    @override
    async def notify_state_entered(self, state: object, income: object) -> None:
        self.__log.info("entered %s %s", state, income)

    @override
    async def notify_income_deferred(self, state: object, income: object) -> None:
        self.__log.info("deferred %s %s", state, income)

    @override
    async def notify_income_recalled(self, state: object, income: object) -> None:
        self.__log.info("recalled %s %s", state, income)

    @override
    async def notify_state_outcome(self, state: object, income: object, outcome: object) -> None:
        self.__log.info("outcome %s %s %s", state, income, outcome)

    @override
    async def notify_state_left(self, state: object, income: object) -> None:
        self.__log.info("left %s %s", state, income)

    @override
    async def notify_state_failed(self, state: object, error: Exception) -> None:
        self.__log.warning("failed %s", state, exc_info=error)

    @override
    async def notify_transition(self, source: object, destination: object) -> None:
        self.__log.info("transitioned from %s to %s", source, destination)

    @override
    async def notify_final(self, state: object) -> None:
        self.__log.info("final %s", state)
