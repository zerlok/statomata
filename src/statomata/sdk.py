import typing as t

from statomata.abc import AsyncStateMachineSubscriber, StateMachineSubscriber
from statomata.executor import AsyncStateMachineExecutor, StateMachineExecutor
from statomata.iterable import (
    AsyncIterableOptStateMachine,
    AsyncIterableSeqStateMachine,
    AsyncIterableState,
    AsyncIterableStateMachine,
    IterableOptStateMachine,
    IterableSeqStateMachine,
    IterableState,
    IterableStateMachine,
)
from statomata.subscriber.registry import AsyncStateMachineSubscriberRegistry, StateMachineSubscriberRegistry
from statomata.unary import (
    AsyncUnaryOptState,
    AsyncUnarySeqState,
    AsyncUnaryState,
    AsyncUnaryStateMachine,
    UnaryOptState,
    UnarySeqState,
    UnaryState,
    UnaryStateMachine,
)

S_contra = t.TypeVar("S_contra", contravariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


def create_sm_executor(
    initial: S_contra,
    fallback: t.Optional[t.Callable[[Exception], t.Optional[S_contra]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[S_contra, U_contra, V_co]]] = None,
) -> StateMachineExecutor[S_contra, U_contra, V_co]:
    return StateMachineExecutor(
        initial, fallback, StateMachineSubscriberRegistry(*subscribers) if subscribers else None
    )


def create_sm_async_executor(
    initial: S_contra,
    fallback: t.Optional[t.Callable[[Exception], t.Optional[S_contra]]] = None,
    subscribers: t.Optional[t.Sequence[AsyncStateMachineSubscriber[S_contra, U_contra, V_co]]] = None,
) -> AsyncStateMachineExecutor[S_contra, U_contra, V_co]:
    return AsyncStateMachineExecutor(
        initial, fallback, AsyncStateMachineSubscriberRegistry(*subscribers) if subscribers else None
    )


def create_unary_sm(
    initial: UnaryState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[UnaryState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[UnaryState[U_contra, V_co], U_contra, V_co]]] = None,
) -> UnaryStateMachine[U_contra, V_co]:
    return UnaryStateMachine(create_sm_executor(initial, fallback, subscribers))


def create_async_unary_sm(
    initial: AsyncUnaryState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[AsyncUnaryState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[
        t.Sequence[AsyncStateMachineSubscriber[AsyncUnaryState[U_contra, V_co], U_contra, V_co]]
    ] = None,
) -> AsyncUnaryStateMachine[U_contra, V_co]:
    return AsyncUnaryStateMachine(create_sm_async_executor(initial, fallback, subscribers))


def create_iterable_sm(
    initial: IterableState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[IterableState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[IterableState[U_contra, V_co], U_contra, V_co]]] = None,
) -> IterableStateMachine[U_contra, V_co]:
    return IterableStateMachine(create_sm_executor(initial, fallback, subscribers))


def create_async_iterable_sm(
    initial: AsyncIterableState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[AsyncIterableState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[
        t.Sequence[AsyncStateMachineSubscriber[AsyncIterableState[U_contra, V_co], U_contra, V_co]]
    ] = None,
) -> AsyncIterableStateMachine[U_contra, V_co]:
    return AsyncIterableStateMachine(create_sm_async_executor(initial, fallback, subscribers))


def create_iterable_opt_sm(
    initial: UnaryOptState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[UnaryOptState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[UnaryOptState[U_contra, V_co], U_contra, V_co]]] = None,
) -> IterableOptStateMachine[U_contra, V_co]:
    return IterableOptStateMachine(create_sm_executor(initial, fallback, subscribers))


def create_async_iterable_opt_sm(
    initial: AsyncUnaryOptState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[AsyncUnaryOptState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[
        t.Sequence[AsyncStateMachineSubscriber[AsyncUnaryOptState[U_contra, V_co], U_contra, V_co]]
    ] = None,
) -> AsyncIterableOptStateMachine[U_contra, V_co]:
    return AsyncIterableOptStateMachine(create_sm_async_executor(initial, fallback, subscribers))


def create_iterable_seq_sm(
    initial: UnarySeqState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[UnarySeqState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[UnarySeqState[U_contra, V_co], U_contra, V_co]]] = None,
) -> IterableSeqStateMachine[U_contra, V_co]:
    return IterableSeqStateMachine(create_sm_executor(initial, fallback, subscribers))


def create_async_iterable_seq_sm(
    initial: AsyncUnarySeqState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[AsyncUnarySeqState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[
        t.Sequence[AsyncStateMachineSubscriber[AsyncUnarySeqState[U_contra, V_co], U_contra, V_co]]
    ] = None,
) -> AsyncIterableSeqStateMachine[U_contra, V_co]:
    return AsyncIterableSeqStateMachine(create_sm_async_executor(initial, fallback, subscribers))
