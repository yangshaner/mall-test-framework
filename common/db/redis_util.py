# common/db/redis_util.py

import redis
import json
import logging
import allure
from typing import Dict, Optional, Any, List
from common.config.config_loader import config

logger = logging.getLogger(__name__)

class RedisUtil:

    def __init__(self):
        redis_config = config.get('redis', {})
        self.pool = redis.ConnectionPool(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_config.get('password', None),
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        logger.info(f"RedisUtil initialized")

    @allure.step("获取Redis值")
    def get(self, key: str) -> Optional[str]:
        value = self.client.get(key)
        logger.debug(f"Redis GET {key} : {value}")
        return value

    @allure.step("设置Redis值")
    def set(self, key: str, value: Any, expire: int = None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        self.client.set(key, value, ex=expire)
        logger.debug(f"Redis SET {key} : {value}")

    def get_json(self, key: str) -> Optional[Dict]:
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return None
        return None

    def set_json(self, key: str, value: Dict, expire: int = None):
        self.set(key, json.dumps(value, ensure_ascii=False), expire)

    @allure.step("删除Redis键")
    def delete(self, *keys):
        result = self.client.delete(*keys)
        logger.debug(f"Redis DELETE {keys} : {result}")
        return result

    @allure.step("检查键是否存在")
    def exists(self, *keys: str) -> bool:
        return self.client.exists(keys) > 0

    def expire(self, key: str, seconds: int):
        self.client.expire(key, seconds)

    def hget(self, *keys: str, field: str) -> Optional[str]:
        return self.client.hget(keys, field)

    def hset(self, *keys: str, field: str, value: Any):
        self.client.hset(keys, field, value)

    def hgetall(self, key: str) -> Dict:
        return self.client.hgetall(key)

    def lpush(self, keys: str, *value):
        return self.client.lpush(keys, *value)

    def rpush(self, key: str, *value):
        return self.client.rpush(key, *value)

    def lpop(self, key: str) -> Optional[str]:
        return self.client.lpop(key)

    def rpop(self, key: str) -> Optional[str]:
        return self.client.rpop(key)

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        return self.client.lrange(key, start, end)

    def sadd(self, key: str, *members):
        return self.client.sadd(key, *members)

    def smembers(self, key: str) -> set:
        return self.client.smembers(key)

    def scard(self, key: str) -> int:
        return self.client.scard(key)

    def incr(self, key: str) -> int:
        return self.client.incr(key)

    def decr(self, key: str) -> int:
        return self.client.decr(key)

    def ttl(self, key: str) -> int:
        return self.client.ttl(key)

    def keys(self, pattern: str = "*") -> List[str]:
        return self.client.keys(pattern)

    def flushdb(self):
        self.client.flushdb()
        logger.warning(f"Redis DB flushed")

    def close(self):
        self.pool.close()
        logger.info(f"Redis connection closed")

redis_util = RedisUtil()