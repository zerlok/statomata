"""
This example demonstrates how to create a traffic light machine using the statomata library.

Adopted from: https://python-statemachine.readthedocs.io/en/latest/auto_examples/order_control_machine.html#sphx-glr-auto-examples-order-control-machine-py
"""

import typing as t
from dataclasses import dataclass

from typing_extensions import assert_never, override

from statomata.abc import Context, StateMachine
from statomata.sdk import create_iterable_opt_sm
from statomata.unary import UnaryOptState


@dataclass(frozen=True)
class OrderItemAdded:
    amount: int


@dataclass(frozen=True)
class OrderPaymentReceived:
    amount: int


@dataclass(frozen=True)
class OrderProcessed:
    pass


@dataclass(frozen=True)
class OrderShipped:
    pass


OrderEvent = t.Union[OrderItemAdded, OrderPaymentReceived, OrderProcessed, OrderShipped]
OrderControlState = UnaryOptState[OrderEvent, str]
OrderControlStateMachine = StateMachine[t.Iterable[OrderEvent], t.Iterable[str]]


class WaitingForPayment(OrderControlState):
    def __init__(self) -> None:
        self.__order_total = 0
        self.__payments = list[int]()

    @override
    def handle(self, income: OrderEvent, context: Context[OrderControlState]) -> str:
        if isinstance(income, OrderItemAdded):
            self.__order_total += income.amount
            return "item added to order"

        elif isinstance(income, OrderPaymentReceived):
            self.__payments.append(income.amount)
            if self.is_payments_enough():
                context.set_state(Processing())
                return "payment received, processing the order"

            return "payment received"

        elif isinstance(income, (OrderProcessed, OrderShipped)):
            return f"can't handle command {income} while waiting for payment"

        else:
            assert_never(income)

    def is_payments_enough(self) -> bool:
        return sum(self.__payments) >= self.__order_total


class Processing(OrderControlState):
    @override
    def handle(self, income: OrderEvent, context: Context[OrderControlState]) -> str:
        if isinstance(income, OrderProcessed):
            context.set_state(Shipping())
            return "the order was processed"

        elif isinstance(income, (OrderItemAdded, OrderPaymentReceived, OrderShipped)):
            return f"can't handle command {income} while processing the order"

        else:
            assert_never(income)


class Shipping(OrderControlState):
    @override
    def handle(self, income: OrderEvent, context: Context[OrderControlState]) -> str:
        if isinstance(income, OrderShipped):
            context.set_finished("order completed")
            return "the order was shipped"

        elif isinstance(income, (OrderItemAdded, OrderPaymentReceived, OrderProcessed)):
            return f"can't handle command {income} while shipping the order"

        else:
            assert_never(income)


def create_order_control_machine() -> OrderControlStateMachine:
    return create_iterable_opt_sm(WaitingForPayment())
