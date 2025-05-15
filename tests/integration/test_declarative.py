import pytest

from statomata.abc import InvalidStateError
from tests.stub.declarative.order_control_machine import Item, OrderController


class TestOrderController:
    @pytest.fixture
    def controller(self) -> OrderController:
        return OrderController()

    def test_do(self, controller: OrderController) -> None:
        controller.add_order_item(Item(1, 20, 10))
        controller.add_order_item(Item(2, 30, 5))
        assert controller.order_total_price == 20 * 10 + 30 * 5

        controller.confirm_order()
        assert not controller.is_payment_enough

        with pytest.raises(InvalidStateError):
            controller.confirm_order()

        with pytest.raises(InvalidStateError):
            controller.add_order_item(Item(-1, -1, -1))

        controller.add_order_payment(100)
        assert controller.current_state is controller.waiting_for_payment
        controller.add_order_payment(200)
        assert controller.current_state is controller.waiting_for_payment
        controller.add_order_payment(50)
        assert controller.current_state is controller.processing
        assert controller.payment_total == 100 + 200 + 50
        assert controller.is_payment_enough

        # FIXME: why mypy thinks statement is unreachable?
        shipment_id = controller.ship_order()  # type: ignore[unreachable]
        controller.complete_order(shipment_id)

        with pytest.raises(InvalidStateError):
            controller.add_order_item(Item(-1, -1, -1))
