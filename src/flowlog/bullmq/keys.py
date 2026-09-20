from fastapi.exceptions import HTTPException

from flowlog.shared.enums.queue_state import QueueState


class BullMQKeys:
    def __init__(self, prefix: str = "bull"):
        self.prefix = prefix

    def meta_pattern(self, queue_name: str) -> str:
        return f"{self.prefix}:{queue_name}:meta"

    def queue_key(self, queue_name: str, state: QueueState | str) -> str:
        self.verify_state(state)

        if isinstance(state, QueueState):
            state = state.value

        return f"{self.prefix}:{queue_name}:{state}"

    def job_key(self, queue_name: str, job_id: str) -> str:
        return f"{self.prefix}:{queue_name}:{job_id}"

    def job_logs_key(self, queue_name: str, job_id: str) -> str:
        return f"{self.prefix}:{queue_name}:{job_id}:logs"

    def job_lock_key(self, queue_name: str, job_id: str) -> str:
        return f"{self.prefix}:{queue_name}:{job_id}:lock"

    def queue_name_from_meta_key(self, key: str) -> str:
        splited_key = key.split(":")

        if len(splited_key) < 3:
            raise HTTPException(status_code=400, detail="Chave meta do bull incorreta")

        splited_key = splited_key[1:-1]
        queue_name = ":".join(splited_key)

        return queue_name

    def verify_state(self, state: str) -> bool:
        try:
            QueueState(state)
            return True
        except ValueError:
            raise ValueError(f"O valor {state} não é um estado válido da fila")
