import pytest

from flowlog.bullmq.keys import BullMQKeys
from flowlog.shared.enums.queue_state import QueueState


@pytest.fixture
def mocked_bullmq_keys() -> BullMQKeys:
    mock = BullMQKeys()
    return mock


def test_default_prefix(mocked_bullmq_keys: BullMQKeys) -> None:
    assert mocked_bullmq_keys.prefix == "bull"


def test_custom_prefix(mocked_bullmq_keys: BullMQKeys) -> None:
    mocked_bullmq_keys.prefix = "prod"

    assert mocked_bullmq_keys.prefix == "prod"


def test_extract_queue_name_from_meta_key(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_name_from_meta_key("bull:payments:retry:meta") should be return payments:retry"""

    queue_name = mocked_bullmq_keys.queue_name_from_meta_key(
        key="bull:payments:retry:meta"
    )

    assert queue_name == "payments:retry"


def test_get_meta_pattern_key(mocked_bullmq_keys: BullMQKeys) -> None:
    """meta_pattern(test-queue) should be return bull:test-queue:meta"""

    meta_key = mocked_bullmq_keys.meta_pattern(queue_name="test-queue")
    assert meta_key == "bull:test-queue:meta"


def test_get_queue_key_with_completed_state(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_key(test-queue,QueueState.COMPLETED) should be return bull:test-queue:completed"""

    state = QueueState.COMPLETED
    queue_key = mocked_bullmq_keys.queue_key(queue_name="test-queue", state=state)

    assert queue_key == "bull:test-queue:completed"


def test_get_queue_key_with_failed_state(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_key(test-queue,QueueState.FAILED) should be return bull:test-queue:failed"""

    state = QueueState.FAILED
    queue_key = mocked_bullmq_keys.queue_key(queue_name="test-queue", state=state)

    assert queue_key == "bull:test-queue:failed"


def test_get_queue_key_with_delayed_state(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_key(test-queue,QueueState.DELAYED) should be return bull:test-queue:delayed"""

    state = QueueState.DELAYED
    queue_key = mocked_bullmq_keys.queue_key(queue_name="test-queue", state=state)

    assert queue_key == "bull:test-queue:delayed"


def test_get_queue_key_with_wait_state(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_key(test-queue,QueueState.WAIT) should be return bull:test-queue:wait"""

    state = QueueState.WAIT
    queue_key = mocked_bullmq_keys.queue_key(queue_name="test-queue", state=state)

    assert queue_key == "bull:test-queue:wait"


def test_get_queue_key_with_prioritized_state(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_key(test-queue,QueueState.PRIORITIZED) should be return bull:test-queue:prioritized"""

    state = QueueState.PRIORITIZED
    queue_key = mocked_bullmq_keys.queue_key(queue_name="test-queue", state=state)

    assert queue_key == "bull:test-queue:prioritized"


def test_get_queue_key_with_invalid_state(mocked_bullmq_keys: BullMQKeys) -> None:
    """queue_key should be throw ValueError exception for invalid queue state"""
    state = "invalid"

    with pytest.raises(
        ValueError, match=f"O valor {state} não é um estado válido da fila"
    ):
        mocked_bullmq_keys.queue_key(queue_name="test-queue", state=state)


def test_get_job_key(mocked_bullmq_keys: BullMQKeys) -> None:
    """job_key should be return a valid job key"""
    job_id = "2234"

    assert (
        mocked_bullmq_keys.job_key(queue_name="test-queue", job_id=job_id)
        == f"bull:test-queue:{job_id}"
    )


def test_job_logs_key(mocked_bullmq_keys: BullMQKeys) -> None:
    """job_logs_key should be return a valid job logs key"""
    job_id = "2234"

    assert (
        mocked_bullmq_keys.job_logs_key(queue_name="test-queue", job_id=job_id)
        == f"bull:test-queue:{job_id}:logs"
    )


def test_job_lock_key(mocked_bullmq_keys: BullMQKeys) -> None:
    """job_lock_key should be return a valid job lock key"""
    job_id = "2234"

    assert (
        mocked_bullmq_keys.job_lock_key(queue_name="test-queue", job_id=job_id)
        == f"bull:test-queue:{job_id}:lock"
    )
