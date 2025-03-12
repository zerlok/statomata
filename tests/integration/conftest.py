import pytest

from tests.stub.order_control_machine import OrderControlStateMachine, create_order_control_machine
from tests.stub.traffic_light_machine import TrafficStateMachine, create_traffic_light_machine


@pytest.fixture
def traffic_light_machine() -> TrafficStateMachine:
    return create_traffic_light_machine()


@pytest.fixture
def order_control_machine() -> OrderControlStateMachine:
    return create_order_control_machine()
