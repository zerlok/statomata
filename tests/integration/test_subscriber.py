import typing as t

import pytest

from statomata.abc import StateMachineAsyncSubscriber, StateMachineSubscriber
from tests.stub.subscriber import SubscriberAsyncStub, SubscriberStub
from tests.stub.traffic_light_machine import (
    AsyncGreen,
    AsyncRed,
    AsyncTrafficState,
    AsyncTrafficStateMachine,
    AsyncYellow,
    CycleEvent,
    GoEvent,
    Green,
    Red,
    TrafficEvent,
    TrafficState,
    TrafficStateMachine,
    Yellow,
)


@pytest.mark.parametrize(
    ("incomes", "expected_events"),
    [
        pytest.param(
            [CycleEvent(), GoEvent(), CycleEvent(), CycleEvent()],
            [
                (Green, "initial"),
                (Green, "state_entered"),
                (Green, "state_outcome"),
                (Green, "state_left"),
                (Green, "transition"),
                (Yellow, "state_entered"),
                (Yellow, "state_outcome"),
                (Yellow, "state_outcome"),
                (Yellow, "state_left"),
                (Yellow, "transition"),
                (Red, "state_entered"),
                (Red, "state_outcome"),
                (Red, "state_left"),
                (Red, "transition"),
            ],
        ),
    ],
)
def test_subscriber_notify_invoked_ok(
    traffic_light_machine: TrafficStateMachine,
    subscriber: SubscriberStub[TrafficState, TrafficEvent, str],
    incomes: t.Sequence[TrafficEvent],
    expected_events: t.Sequence[tuple[type[TrafficState], str]],
) -> None:
    for income in incomes:
        traffic_light_machine.run(income)

    assert [(type(state), name) for state, name in subscriber.events] == expected_events


@pytest.mark.parametrize(
    ("incomes", "expected_events"),
    [
        pytest.param(
            [CycleEvent(), GoEvent(), CycleEvent(), CycleEvent()],
            [
                (AsyncGreen, "initial"),
                (AsyncGreen, "state_entered"),
                (AsyncGreen, "state_outcome"),
                (AsyncGreen, "state_left"),
                (AsyncGreen, "transition"),
                (AsyncYellow, "state_entered"),
                (AsyncYellow, "state_outcome"),
                (AsyncYellow, "state_outcome"),
                (AsyncYellow, "state_left"),
                (AsyncYellow, "transition"),
                (AsyncRed, "state_entered"),
                (AsyncRed, "state_outcome"),
                (AsyncRed, "state_left"),
                (AsyncRed, "transition"),
            ],
        ),
    ],
)
async def test_subscriber_async_notify_invoked_ok(
    traffic_light_machine_async: AsyncTrafficStateMachine,
    subscriber_async: SubscriberAsyncStub[AsyncTrafficState, TrafficEvent, str],
    incomes: t.Sequence[TrafficEvent],
    expected_events: t.Sequence[tuple[type[AsyncTrafficState], str]],
) -> None:
    for income in incomes:
        await traffic_light_machine_async.run(income)

    assert [(type(state), name) for state, name in subscriber_async.events] == expected_events


@pytest.fixture
def subscriber() -> SubscriberStub[TrafficState, TrafficEvent, str]:
    return SubscriberStub[TrafficState, TrafficEvent, str]()


@pytest.fixture
def traffic_light_subscribers(
    subscriber: SubscriberStub[TrafficState, TrafficEvent, str],
) -> t.Sequence[StateMachineSubscriber[TrafficState, TrafficEvent, str]]:
    return [subscriber]


@pytest.fixture
def subscriber_async() -> SubscriberAsyncStub[AsyncTrafficState, TrafficEvent, str]:
    return SubscriberAsyncStub[AsyncTrafficState, TrafficEvent, str]()


@pytest.fixture
def traffic_light_subscribers_async(
    subscriber_async: SubscriberAsyncStub[AsyncTrafficState, TrafficEvent, str],
) -> t.Sequence[StateMachineAsyncSubscriber[AsyncTrafficState, TrafficEvent, str]]:
    return [subscriber_async]
