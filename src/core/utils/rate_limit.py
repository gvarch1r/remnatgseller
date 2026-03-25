from redis.asyncio import Redis


async def is_rate_limited(redis: Redis, scope: str, user_id: int, cooldown_sec: int) -> bool:
    """
    Per-user cooldown using SET NX EX.
    Returns True if the action should be blocked (key already exists).
    """
    key = f"rl:{scope}:{user_id}"
    was_set = await redis.set(key, "1", nx=True, ex=max(1, int(cooldown_sec)))
    # redis-py: True if key was set, None if NX prevented (key already exists)
    return was_set is None
