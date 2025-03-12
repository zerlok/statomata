"""
This example demonstrates how to create a traffic light machine using the statomata library.

Adopted from: https://python-statemachine.readthedocs.io/en/latest/auto_examples/traffic_light_machine.html#sphx-glr-auto-examples-traffic-light-machine-py
"""

import typing as t
from dataclasses import dataclass

from typing_extensions import assert_never, override

from statomata.abc import Context, StateMachine
from statomata.sdk import create_unary_sm
from statomata.unary import UnaryState


@dataclass(frozen=True)
class GoEvent:
    pass


@dataclass(frozen=True)
class CycleEvent:
    pass


TrafficEvent = t.Union[GoEvent, CycleEvent]
TrafficState = UnaryState[TrafficEvent, str]
TrafficStateMachine = StateMachine[TrafficEvent, str]


class Green(TrafficState):
    @override
    def handle(self, income: TrafficEvent, context: Context[TrafficState]) -> str:
        if isinstance(income, GoEvent):
            return "you can go"

        elif isinstance(income, CycleEvent):
            context.set_state(Yellow())
            return "switched to yellow"

        else:
            assert_never(income)


class Yellow(TrafficState):
    @override
    def handle(self, income: TrafficEvent, context: Context[TrafficState]) -> str:
        if isinstance(income, GoEvent):
            return "you may go on your own risk"

        elif isinstance(income, CycleEvent):
            context.set_state(Red())
            return "switched to red"

        else:
            assert_never(income)


class Red(TrafficState):
    @override
    def handle(self, income: TrafficEvent, context: Context[TrafficState]) -> str:
        if isinstance(income, GoEvent):
            return "you can't go!"

        elif isinstance(income, CycleEvent):
            context.set_state(Green())
            return "switched to green"

        else:
            assert_never(income)


def create_traffic_light_machine() -> TrafficStateMachine:
    return create_unary_sm(Green())
