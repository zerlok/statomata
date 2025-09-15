import typing as t

import pytest
from anyio import create_memory_object_stream, create_task_group
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from examples.state_machines.anyio_cases import ProcessingState, ProcessMessage, StopMessage, StreamMessage
from statomata.anyio import AnyioStreamStateMachine, create_anyio_sm


class MemoryStreams(t.NamedTuple):
    input_send: MemoryObjectSendStream[StreamMessage]
    input_receive: MemoryObjectReceiveStream[StreamMessage]
    output_send: MemoryObjectSendStream[str]
    output_receive: MemoryObjectReceiveStream[str]


@pytest.mark.parametrize(
    ("inputs", "expected_outputs"),
    [
        pytest.param(
            [
                ProcessMessage(5),
                ProcessMessage(15),
                ProcessMessage(3),
                StopMessage(),
            ],
            [
                "Processing: 5",
                "Processing: 15",
                "Large value detected",
                "Processing: 3",
                "Stopping processing",
            ],
            id="basic_processing_with_large_value",
        ),
        pytest.param(
            [
                ProcessMessage(5),
                ProcessMessage(-1),
                ProcessMessage(3),
                StopMessage(),
            ],
            [
                "Processing: 5",
                "Processing: -1",
                "Negative value, switching to error state",
                "Error: Cannot process 3 in error state",
                "Stopping in error state",
            ],
            id="state_transition_to_error",
        ),
        pytest.param(
            [
                ProcessMessage(1),
                ProcessMessage(2),
                StopMessage(),
                ProcessMessage(3),
            ],
            [
                "Processing: 1",
                "Processing: 2",
                "Stopping processing",
            ],
            id="abort_on_stop_message",
        ),
    ],
)
async def test_anyio_stream_state_machine_processes_inputs(
    sm: AnyioStreamStateMachine[StreamMessage, str],
    memory_streams: MemoryStreams,
    inputs: t.Sequence[StreamMessage],
    expected_outputs: t.Sequence[str],
) -> None:
    outputs = await run_machine(sm, memory_streams, inputs)
    assert outputs == list(expected_outputs)


async def run_machine(
    sm: AnyioStreamStateMachine[StreamMessage, str],
    streams: MemoryStreams,
    inputs: t.Sequence[StreamMessage],
) -> t.Sequence[str]:
    async with create_task_group() as tg:
        tg.start_soon(send_inputs, streams, inputs)
        tg.start_soon(sm.run, streams.input_receive, streams.output_send)
        outputs = await collect_outputs(streams)

    # NOTE: mypy false-positive missing return statement, see: https://github.com/python/mypy/issues/19849
    return outputs


@pytest.fixture
def sm() -> AnyioStreamStateMachine[StreamMessage, str]:
    return create_anyio_sm(ProcessingState())


@pytest.fixture
def memory_streams(inputs: t.Sequence[StreamMessage], expected_outputs: t.Sequence[str]) -> MemoryStreams:
    input_send, input_receive = create_memory_object_stream[StreamMessage](max_buffer_size=len(inputs) * 2)
    output_send, output_receive = create_memory_object_stream[str](max_buffer_size=len(expected_outputs) * 2)
    return MemoryStreams(input_send, input_receive, output_send, output_receive)


async def send_inputs(streams: MemoryStreams, inputs: t.Sequence[StreamMessage]) -> None:
    async with streams.input_send:
        for message in inputs:
            await streams.input_send.send(message)


async def collect_outputs(streams: MemoryStreams) -> t.Sequence[str]:
    outputs: list[str] = []

    async with streams.output_receive:
        outputs.extend([output async for output in streams.output_receive])

    return outputs
