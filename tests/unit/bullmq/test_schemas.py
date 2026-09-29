import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from flowlog.bullmq.schemas import BullJob
from flowlog.shared.enums.bull_state_enums import BullState

FIXTURES_DIR = Path(__file__).parent / "fixtures"

RawJobHash = dict[str, str]
LoadJobs = Callable[[str], RawJobHash]

_TRACE_BASE = (
    r"C:\Users\geris\orca\workspaces\flowlog\docs-ticket-03\examples\bullmq-test"
)
_WORKER_JS = _TRACE_BASE + r"\node_modules\bullmq\dist\cjs\classes\worker.js"
EXPECTED_STACK_TRACE = "\n".join(
    [
        "Error: Job de erro",
        rf"    at <anonymous> ({_TRACE_BASE}\src\workers\test-worker.ts:25:17)",
        f"    at <anonymous> ({_WORKER_JS}:582:43)",
        f"    at processJob ({_WORKER_JS}:565:21)",
        f"    at mainLoop ({_WORKER_JS}:330:41)",
        f"    at async run ({_WORKER_JS}:263:19)",
        rf"    at async main ({_TRACE_BASE}\capture.ts:8:16)",
        "    at processTicksAndRejections (native:7:39)",
    ]
)


@pytest.fixture
def load_jobs() -> LoadJobs:
    """Retorna uma função para carregar qualquer JSON na pasta fixtures."""

    def _load(file_name: str) -> RawJobHash:
        with open(FIXTURES_DIR / file_name, encoding="utf-8") as file:
            return json.load(file)

    return _load


def test_create_waited_job(load_jobs: LoadJobs) -> None:
    bull_waited_job_json = load_jobs("wait.json")
    bull_job = BullJob.model_validate(bull_waited_job_json | {"state": BullState.WAIT})

    assert bull_job.name == "quickly-job"
    assert bull_job.data["message"] == "Job rápido iniciado"
    assert bull_job.opts["attempts"] == 0
    assert bull_job.opts["priority"] == 0
    assert bull_job.timestamp == datetime(2026, 9, 15, 1, 58, 48, 735000, tzinfo=UTC)
    assert bull_job.state == BullState.WAIT
    assert bull_job.duration is None
    assert bull_job.wait_time is None
    assert bull_job.processed_on is None
    assert bull_job.finished_on is None
    assert bull_job.failed_reason is None
    assert bull_job.return_value is None
    assert bull_job.attempts_made == 0
    assert bull_job.stack_trace == []


def test_create_waited_job_with_invalid_timestamp(load_jobs: LoadJobs) -> None:
    bull_waited_job_json = load_jobs("wait.json")

    with pytest.raises(ValueError, match="Utilize um timestamp válido"):
        BullJob.model_validate(
            bull_waited_job_json | {"state": BullState.WAIT, "timestamp": "131321_#2"}
        )


def test_create_delayed_job(load_jobs: LoadJobs) -> None:
    bull_delayed_job_json = load_jobs("delay.json")
    bull_job = BullJob.model_validate(
        bull_delayed_job_json | {"state": BullState.DELAYED}
    )

    assert bull_job.name == "delay-job"
    assert bull_job.data["message"] == "Job com delay iniciado"
    assert bull_job.opts["attempts"] == 0
    assert bull_job.opts["priority"] == 0
    assert bull_job.opts["delay"] == 10000
    assert bull_job.state == BullState.DELAYED
    assert bull_job.duration is None
    assert bull_job.wait_time is None
    assert bull_job.processed_on is None
    assert bull_job.finished_on is None
    assert bull_job.failed_reason is None
    assert bull_job.return_value is None
    assert bull_job.attempts_made == 0
    assert bull_job.stack_trace == []


def test_create_delayed_job_without_delay(load_jobs: LoadJobs) -> None:
    bull_delayed_job_json = load_jobs("invalid-delay.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado delayed é necessário informar o delay em opts",
    ):
        BullJob.model_validate(bull_delayed_job_json | {"state": BullState.DELAYED})


def test_create_delayed_job_with_zero_delay(load_jobs: LoadJobs) -> None:
    bull_delayed_job_json = load_jobs("zero-delay.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado delayed o valor do delay deve ser maior que zero",
    ):
        BullJob.model_validate(
            bull_delayed_job_json
            | {
                "state": BullState.DELAYED,
            }
        )


def test_create_active_job(load_jobs: LoadJobs) -> None:
    bull_active_job_json = load_jobs("active.json")
    bull_job = BullJob.model_validate(
        bull_active_job_json | {"state": BullState.ACTIVE}
    )

    assert bull_job.name == "slowly-job"
    assert bull_job.data["message"] == "Job lento iniciado"
    assert bull_job.opts["attempts"] == 0
    assert bull_job.opts["priority"] == 0
    assert bull_job.state == BullState.ACTIVE
    assert bull_job.timestamp == datetime(2026, 9, 15, 1, 55, 12, 357000, tzinfo=UTC)
    assert bull_job.processed_on == datetime(2026, 9, 15, 1, 55, 49, 695000, tzinfo=UTC)
    assert bull_job.wait_time == timedelta(seconds=37, microseconds=338000)
    assert bull_job.duration is None
    assert bull_job.finished_on is None
    assert bull_job.failed_reason is None
    assert bull_job.return_value is None
    assert bull_job.attempts_made == 0
    assert bull_job.stack_trace == []


def test_create_active_job_without_processed_on(load_jobs: LoadJobs) -> None:
    bull_active_job_json = load_jobs("invalid-active.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado active é necessário informar o processedOn",
    ):
        BullJob.model_validate(bull_active_job_json | {"state": BullState.ACTIVE})


def test_create_completed_job(load_jobs: LoadJobs) -> None:
    bull_completed_job_json = load_jobs("completed.json")
    bull_job = BullJob.model_validate(
        bull_completed_job_json | {"state": BullState.COMPLETED}
    )

    assert bull_job.name == "quickly-job"
    assert bull_job.data["message"] == "Job rápido iniciado"
    assert bull_job.opts["attempts"] == 0
    assert bull_job.opts["priority"] == 0
    assert bull_job.state == BullState.COMPLETED
    assert bull_job.timestamp == datetime(2026, 9, 15, 1, 55, 12, 277000, tzinfo=UTC)
    assert bull_job.processed_on == datetime(2026, 9, 15, 1, 55, 49, 680000, tzinfo=UTC)
    assert bull_job.finished_on == datetime(2026, 9, 15, 1, 55, 49, 717000, tzinfo=UTC)
    assert bull_job.wait_time == timedelta(seconds=37, microseconds=403000)
    assert bull_job.duration == timedelta(microseconds=37000)
    assert bull_job.attempts_made == 1
    assert bull_job.return_value == "success"
    assert bull_job.failed_reason is None
    assert bull_job.stack_trace == []


def test_create_completed_job_without_processed_on(load_jobs: LoadJobs) -> None:
    bull_completed_job_json = load_jobs("without-processed-on-completed.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado completed é necessário informar o processedOn",
    ):
        BullJob.model_validate(bull_completed_job_json | {"state": BullState.COMPLETED})


def test_create_completed_job_without_finished_on(load_jobs: LoadJobs) -> None:
    bull_completed_job_json = load_jobs("invalid-completed.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado completed é necessário informar o finishedOn",
    ):
        BullJob.model_validate(bull_completed_job_json | {"state": BullState.COMPLETED})


def test_create_failed_job(load_jobs: LoadJobs) -> None:
    bull_failed_job_json = load_jobs("failed.json")
    bull_job = BullJob.model_validate(
        bull_failed_job_json | {"state": BullState.FAILED}
    )

    assert bull_job.name == "error-job"
    assert bull_job.data["message"] == "Job de erro iniciado"
    assert bull_job.opts["attempts"] == 3
    assert bull_job.opts["priority"] == 0
    assert bull_job.opts["backoff"]["delay"] == 5000
    assert bull_job.opts["backoff"]["type"] == "exponential"
    assert bull_job.state == BullState.FAILED
    assert bull_job.timestamp == datetime(2026, 9, 15, 1, 55, 12, 361000, tzinfo=UTC)
    assert bull_job.processed_on == datetime(2026, 9, 15, 1, 56, 4, 860000, tzinfo=UTC)
    assert bull_job.finished_on == datetime(2026, 9, 15, 1, 56, 4, 905000, tzinfo=UTC)
    assert bull_job.wait_time == timedelta(seconds=52, microseconds=499000)
    assert bull_job.duration == timedelta(microseconds=45000)
    assert bull_job.attempts_made == 3
    assert bull_job.failed_reason == "Job de erro"
    assert len(bull_job.stack_trace) == 3
    assert bull_job.stack_trace == [EXPECTED_STACK_TRACE] * 3
    assert bull_job.return_value is None


def test_create_failed_job_without_processed_on(load_jobs: LoadJobs) -> None:
    bull_failed_job_json = load_jobs("without-processed-on-failed.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado failed é necessário informar o processedOn",
    ):
        BullJob.model_validate(bull_failed_job_json | {"state": BullState.FAILED})


def test_create_failed_job_without_finished_on(load_jobs: LoadJobs) -> None:
    bull_completed_job_json = load_jobs("without-finish-on-failed.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado failed é necessário informar o finishedOn",
    ):
        BullJob.model_validate(bull_completed_job_json | {"state": BullState.FAILED})


def test_create_failed_job_without_failed_reason(load_jobs: LoadJobs) -> None:
    bull_completed_job_json = load_jobs("without-failed-reason-failed.json")

    with pytest.raises(
        ValueError,
        match="Para jobs com o estado failed é necessário informar o failedReason",
    ):
        BullJob.model_validate(bull_completed_job_json | {"state": BullState.FAILED})
