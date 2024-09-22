import aioredis
import os
from dotenv import load_dotenv

load_dotenv()


class RedisHandler:
    def __init__(self):
        self.redis = aioredis.from_url(
            f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
        )

    async def create_user_session(self, username):
        uid = self.generate_random_uid()
        await self.redis.set(uid, username, ex=3600)  # 设置1小时过期
        return uid

    async def get_user_session(self, uid):
        return await self.redis.get(uid)

    def generate_random_uid(self):
        import uuid

        return str(uuid.uuid4())
