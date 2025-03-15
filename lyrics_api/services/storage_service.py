import redis.asyncio as redis


class StorageServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class StorageService:
    def __init__(self, client: redis.Redis):
        self.client = client

    async def store_item(self, key: str, value):
        try:
            await self.client.set(name=key, value=value)
        except Exception as e:
            print(f"An exception occurred while trying to store {key}:{value} - {e}")
            raise StorageServiceException(f"An exception occurred while trying to store {key}:{value} - {e}")

    async def retrieve_item(self, key: str):
        try:
            item = await self.client.get(key)
            return item
        except Exception as e:
            print(f"An exception occurred while trying to retrieve {key} - {e}")
            raise StorageServiceException(f"An exception occurred while trying to retrieve {key} - {e}")
