from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


client = AsyncIOMotorClient(settings.mongo_url)
db = client[settings.db_name]


async def close_db() -> None:
    client.close()

