from redis.asyncio.client import Redis


class RedisClient:
    _client: Redis | None = None

    @classmethod
    async def get_client(cls) -> Redis:
        """Returns the Redis client."""

        if cls._client is None:
            client = Redis(host="localhost", port=6379, decode_responses=True)

            cls._client = client

        is_connected = await cls._client.ping()
        if not is_connected:
            raise ConnectionError("Failed to connect to Redis")

        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Closes the Redis client."""
        if cls._client:
            await cls._client.close()
            cls._client = None
