import typing as t

from statomata.abc import StateMachine, StateMachineAsyncSubscriber, StateMachineSubscriber
from statomata.executor import AsyncStateMachineExecutor, StateMachineExecutor
from statomata.iterable import (
    AsyncIterableState,
    AsyncIterableStateMachine,
    IterableOptStateMachine,
    IterableState,
    IterableStateMachine,
)
from statomata.subscriber import StateMachineAsyncSubscriberRegistry, StateMachineSubscriberRegistry
from statomata.unary import AsyncUnaryState, AsyncUnaryStateMachine, UnaryOptState, UnaryState, UnaryStateMachine

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
    subscribers: t.Optional[t.Sequence[StateMachineAsyncSubscriber[S_contra, U_contra, V_co]]] = None,
) -> AsyncStateMachineExecutor[S_contra, U_contra, V_co]:
    return AsyncStateMachineExecutor(
        initial, fallback, StateMachineAsyncSubscriberRegistry(*subscribers) if subscribers else None
    )


def create_unary_sm(
    initial: UnaryState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[UnaryState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[UnaryState[U_contra, V_co], U_contra, V_co]]] = None,
) -> StateMachine[U_contra, V_co]:
    return UnaryStateMachine(create_sm_executor(initial, fallback, subscribers))


def create_async_unary_sm(
    initial: AsyncUnaryState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[AsyncUnaryState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[
        t.Sequence[StateMachineAsyncSubscriber[AsyncUnaryState[U_contra, V_co], U_contra, V_co]]
    ] = None,
) -> StateMachine[U_contra, t.Awaitable[V_co]]:
    return AsyncUnaryStateMachine(create_sm_async_executor(initial, fallback, subscribers))


def create_iterable_sm(
    initial: IterableState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[IterableState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[IterableState[U_contra, V_co], U_contra, V_co]]] = None,
) -> StateMachine[t.Iterable[U_contra], t.Iterable[V_co]]:
    return IterableStateMachine(create_sm_executor(initial, fallback, subscribers))


def create_async_iterable_sm(
    initial: AsyncIterableState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[AsyncIterableState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[
        t.Sequence[StateMachineAsyncSubscriber[AsyncIterableState[U_contra, V_co], U_contra, V_co]]
    ] = None,
) -> StateMachine[t.AsyncIterable[U_contra], t.AsyncIterable[V_co]]:
    return AsyncIterableStateMachine(create_sm_async_executor(initial, fallback, subscribers))


def create_iterable_opt_sm(
    initial: UnaryOptState[U_contra, V_co],
    fallback: t.Optional[t.Callable[[Exception], t.Optional[UnaryOptState[U_contra, V_co]]]] = None,
    subscribers: t.Optional[t.Sequence[StateMachineSubscriber[UnaryOptState[U_contra, V_co], U_contra, V_co]]] = None,
) -> StateMachine[t.Iterable[U_contra], t.Iterable[V_co]]:
    return IterableOptStateMachine(create_sm_executor(initial, fallback, subscribers))
