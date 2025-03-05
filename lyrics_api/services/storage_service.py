import redis.asyncio as redis


class StorageService:
    def __init__(self, client: redis.Redis):
        self.client = client

    async def store_item(self, key: str, value):
        await self.client.set(name=key, value=value)

    async def store_items(self, items: dict):
        await self.client.mset(items)

    async def retrieve_item(self, key: str):
        return await self.client.get(key)

    async def retrieve_items(self, keys: list[str]) -> list:
        return await self.client.mget(keys)
