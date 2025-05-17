import pytest

from statomata.exception import InvalidStateError
from tests.stub.declarative.order_control import Item, OrderController
from tests.stub.declarative.store import PositiveNumberStore
from tests.stub.declarative.transitions import Transitions


class TestOrderController:
    @pytest.fixture
    def sm(self) -> OrderController:
        return OrderController()

    def test_do(self, sm: OrderController) -> None:
        sm.add_order_item(Item(1, 20, 10))
        sm.add_order_item(Item(2, 30, 5))
        assert sm.order_total_price == 20 * 10 + 30 * 5

        sm.confirm_order()
        assert not sm.is_payment_enough

        with pytest.raises(InvalidStateError):
            sm.confirm_order()

        with pytest.raises(InvalidStateError):
            sm.add_order_item(Item(-1, -1, -1))

        sm.add_order_payment(100)
        assert sm.current_state is sm.waiting_for_payment
        sm.add_order_payment(200)
        assert sm.current_state is sm.waiting_for_payment
        sm.add_order_payment(50)
        assert sm.current_state is sm.processing
        assert sm.payment_total == 100 + 200 + 50
        assert sm.is_payment_enough

        # FIXME: why mypy thinks statement is unreachable?
        shipment_id = sm.ship_order()  # type: ignore[unreachable]
        sm.complete_order(shipment_id)

        with pytest.raises(InvalidStateError):
            sm.add_order_item(Item(-1, -1, -1))


class TestPositiveNumberStore:
    @pytest.fixture
    def sm(self) -> PositiveNumberStore:
        return PositiveNumberStore()

    def test_do(self, sm: PositiveNumberStore) -> None:
        assert sm.current_state is sm.idle

        sm.open()
        assert sm.current_state is sm.opened

        sm.open()  # already opened
        sm.extend(1, 2, 3)
        sm.open()  # already opened
        sm.extend(4, 5)

        assert sm.values == [1, 2, 3, 4, 5]

        # fallback to broken state
        sm.extend(6, -1, 7)

        assert sm.current_state is sm.broken

        # can't extend in broken state
        with pytest.raises(InvalidStateError):
            sm.extend(-5)

        sm.recover()
        assert sm.current_state is sm.opened
        assert sm.values == [1, 2, 3, 4, 5, 6, 7]

        sm.recover()  # is not broken

        result = sm.close()
        assert sm.current_state is sm.closed
        assert result == sm.values

        result2 = sm.close()  # already closed
        assert result2 == result


class TestTransitions:
    @pytest.fixture
    def sm(self) -> Transitions:
        return Transitions()

    def test_do(self, sm: Transitions) -> None:
        sm.from_ace_to_bdf()
        sm.from_b_to_c()
        sm.from_ace_to_bdf()

        with pytest.raises(InvalidStateError):
            sm.from_ace_to_bdf()
