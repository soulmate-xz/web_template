import hashlib
import pickle
from functools import wraps
from typing import Any, AnyStr, Callable, Optional, TypeVar, Union

from redis import asyncio as aioredis
from starlette.responses import Response

from backend.app.core.config import settings
from backend.app.core.models.user import User as UserORM
from backend.app.core.schemas import RWModel

RedisKey = TypeVar("RedisKey", str, bytes)
RedisValue = Union[AnyStr, float, int]


class RedisCache:
    _client: aioredis.Redis = aioredis.from_url(settings.BACKEND_URL)

    @classmethod
    async def get(
        cls,
        key: RedisKey,
        default: Optional[RedisValue] = None,
    ) -> bytes:
        cached_value = await cls._client.get(key)

        return cached_value if cached_value is not None else default  # type: ignore

    @classmethod
    async def set(
        cls,
        key: RedisKey,
        value: RedisValue,
        **kwargs: Any,
    ) -> Optional[bool]:
        return await cls._client.set(key, value, **kwargs)

    @classmethod
    async def incr(cls, key: RedisKey, amount: int = 1) -> int:
        return await cls._client.incr(key, amount)

    @classmethod
    async def delete(cls, key: RedisKey) -> bool:
        return bool(await cls._client.delete(key))

    @classmethod
    async def close(cls) -> None:
        await cls._client.aclose()


def CacheKeyBuilder(
    func: Callable,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
) -> str:
    prefix = "backend:response:cache:"
    request = ""
    user = ""
    if kwargs and kwargs.get("request"):
        request = kwargs.get("request")  # type: ignore
        if isinstance(request, RWModel):
            request = request.json()
        user = kwargs.get("user")  # type: ignore
        if isinstance(user, UserORM):
            user = user.id  # type: ignore
    cache_key = (
        prefix
        + hashlib.md5(f"{func.__module__}:{func.__name__}:{request}:{user}".encode("utf-8")).hexdigest()  # nosec:B303
    )
    return cache_key


class CacheEncoder:
    @classmethod
    def encode(cls, value: Response) -> RedisValue:
        return pickle.dumps(value)

    @classmethod
    def decode(cls, value: bytes) -> Response:
        return pickle.loads(value)


def cache(expire: Optional[int] = None) -> Callable:
    """
    cache all function
    :param expire:
    :return:
    """

    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            copy_kwargs = kwargs.copy()
            cache_key = CacheKeyBuilder(func, args=args, kwargs=copy_kwargs)
            # 这里可以从request中获取请求参数, 但是需要如果需要用户权限等级鉴定的接口禁止使用cache装饰。
            # FIXME 对 stream response进行缓存
            cached = await RedisCache.get(cache_key)
            if not cached or settings.TESTING:
                res = await func(*args, **kwargs)
                await RedisCache.set(key=cache_key, value=CacheEncoder.encode(res), ex=expire)
                return res
            else:
                return CacheEncoder.decode(cached)

        return inner

    return wrapper
