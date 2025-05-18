"""
Adopted from: https://python-statemachine.readthedocs.io/en/latest/auto_examples/order_control_machine.html#sphx-glr-auto-examples-order-control-machine-py
"""

import typing as t
from dataclasses import dataclass

from statomata.declarative.builder import State
from statomata.declarative.state_machine import DeclarativeStateMachine


@dataclass(frozen=True)
class Item:
    id_: int
    price: int
    amount: int


class OrderController(DeclarativeStateMachine):
    waiting_for_order = State(initial=True)
    waiting_for_payment = State()
    processing = State()
    shipping = State()
    completed = State(final=True)

    def __init__(self) -> None:
        super().__init__()

        self.__items = list[Item]()
        self.__payments = list[int]()
        self.__shipment_id: t.Optional[str] = None

    @property
    def is_order_empty(self) -> bool:
        return not self.__items

    @property
    def order_total_price(self) -> int:
        return sum(item.price * item.amount for item in self.__items)

    @property
    def payment_total(self) -> int:
        return sum(self.__payments)

    @property
    def is_payment_enough(self) -> bool:
        return self.payment_total >= self.order_total_price

    @waiting_for_order
    def add_order_item(self, item: Item) -> None:
        self.__items.append(item)

    @waiting_for_order.to(waiting_for_payment).when_not(is_order_empty)
    def confirm_order(self) -> None:
        pass

    @waiting_for_payment.to(processing).when(is_payment_enough)
    def add_order_payment(self, amount: int) -> None:
        self.__payments.append(amount)

    @processing.to(shipping)
    def ship_order(self) -> str:
        self.__shipment_id = "secret123"
        return self.__shipment_id

    @shipping.to(completed)
    def complete_order(self, shipment_id: str) -> None:
        if shipment_id != self.__shipment_id:
            raise ValueError(shipment_id)
