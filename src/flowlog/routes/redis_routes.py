from fastapi import APIRouter

from flowlog.bullmq.client import RedisClient
from flowlog.bullmq.keys import BullMQKeys
from flowlog.shared.enums.queue_state import QueueState

redis_router = APIRouter(prefix="/redis")


@redis_router.get("/ping")
async def ping_redis():
    redis = await RedisClient.get_client()
    is_ping = await redis.ping()

    bullmq_keys = BullMQKeys(prefix="bull")

    queue_key = bullmq_keys.queue_key(
        queue_name="test-queue", state=QueueState.COMPLETED
    )
    print(queue_key)

    meta_key = bullmq_keys.meta_pattern(queue_name="test:queue")
    print(bullmq_keys.queue_name_from_meta_key(key="bull:pagamentos:retry:meta"))

    return {"message": is_ping}
