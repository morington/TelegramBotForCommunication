import asyncio
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager

import ormsgpack
import structlog
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.errors import BucketNotFoundError
from nats.js.kv import KeyValue
from nats.errors import TimeoutError as NatsTimeoutError


logger = structlog.getLogger("NATS")


class NatsClient:
    """NATS client connection manager with JetStream and KV support."""

    def __init__(self, servers: str) -> None:
        """
        Initialize NATS client with server address.

        Args:
            servers: NATS server connection string (e.g., "nats://localhost:4222")
        """
        self._servers = servers
        self._client = Client()
        self._js: Optional[JetStreamContext] = None
        self._is_connected = False
        self._kv_stores: Dict[str, KeyValue] = {}  # Cache for KV stores

    @property
    def jetstream(self) -> JetStreamContext:
        """Get JetStream context, raising an error if not connected."""
        if not self._js:
            raise ValueError("JetStream is not connected. Call connect() first.")
        return self._js

    @property
    def is_connected(self) -> bool:
        """Check if the client is currently connected."""
        return self._is_connected

    async def connect(self) -> None:
        """Establish connection to NATS server and initialize JetStream."""
        if self._is_connected:
            await logger.awarning("Already connected to NATS")
            return

        await self._client.connect(servers=self._servers)
        self._js = self._client.jetstream()
        self._is_connected = True
        await logger.ainfo(f"Connected to NATS at {self._servers}")

    async def disconnect(self) -> None:
        """Gracefully disconnect from NATS server and clean up resources."""
        if not self._is_connected:
            return

        await self._client.close()
        self._is_connected = False
        self._js = None
        self._kv_stores.clear()
        await logger.ainfo("Disconnected from NATS")

    @asynccontextmanager
    async def connection(self):
        """Async context manager for managing NATS connection lifecycle."""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    async def ensure_kv_bucket_exists(self, bucket_name: str) -> None:
        """
        Ensure that a given KV bucket exists.

        Args:
            bucket_name: Name of the KV bucket to check

        Raises:
            BucketNotFoundError: If the bucket does not exist
            ValueError: If not connected to JetStream
        """
        if not self._is_connected:
            raise ValueError("Must be connected to NATS to check KV bucket")

        try:
            await self.jetstream.key_value(bucket_name)
            await logger.adebug(f"KV bucket `{bucket_name}` exists")
        except BucketNotFoundError:
            await logger.aerror(f"KV bucket `{bucket_name}` does not exist")
            raise

    async def get_or_create_kv_bucket(self, bucket_name: str, history: int = 10) -> KeyValue:
        """
        Get an existing KV bucket or create it if it doesn't exist.

        Args:
            bucket_name: Name of the KV bucket to access or create
            history: Number of historical values to keep (default: 10)

        Returns:
            KeyValue: NATS KV store instance

        Raises:
            ValueError: If not connected to JetStream
            Exception: If bucket cannot be created or accessed
        """
        if not self._is_connected:
            raise ValueError("Must be connected to NATS to access KV bucket")

        if bucket_name in self._kv_stores:
            return self._kv_stores[bucket_name]

        try:
            # First try to get existing bucket
            kv = await self.jetstream.key_value(bucket_name)
            await logger.ainfo(f"Accessed existing KV bucket: {bucket_name}")
        except BucketNotFoundError:
            # If it doesn't exist, create it
            try:
                kv = await self.jetstream.create_key_value(bucket=bucket_name, history=history)
                await logger.ainfo(f"Created new KV bucket: {bucket_name} with history={history}")
            except Exception as e:
                await logger.aerror(f"Failed to create KV bucket `{bucket_name}`: {str(e)}")
                raise

        self._kv_stores[bucket_name] = kv
        return kv

    async def put_kv(
            self,
            bucket_name: str,
            key: str,
            value: Any
    ) -> None:
        """
        Put a value into a KV bucket using ormsgpack serialization.

        Args:
            bucket_name: Name of the KV bucket
            key: Key to store the value under
            value: Value to store (will be serialized with ormsgpack)
            timeout: Operation timeout in seconds

        Raises:
            NatsTimeoutError: If operation times out
            ValueError: If bucket doesn't exist or client not connected
        """
        await logger.adebug("1")
        kv = await self.get_or_create_kv_bucket(bucket_name)
        await logger.adebug("2")
        serialized_value = ormsgpack.packb(value)
        await logger.adebug("3")
        await kv.put(key, serialized_value)
        await logger.adebug(f"Stored value in KV bucket `{bucket_name}` under key `{key}`")

    async def get_kv(
            self,
            bucket_name: str,
            key: str
    ) -> Optional[Any]:
        """
        Get a value from a KV bucket and deserialize it with ormsgpack.

        Args:
            bucket_name: Name of the KV bucket
            key: Key to retrieve
            timeout: Operation timeout in seconds

        Returns:
            Optional[Any]: Deserialized value or None if key doesn't exist

        Raises:
            NatsTimeoutError: If operation times out
            ValueError: If bucket doesn't exist or client not connected
        """
        kv = await self.get_or_create_kv_bucket(bucket_name)
        try:
            entry = await kv.get(key)
            if entry and entry.value:
                return ormsgpack.unpackb(entry.value)
            return None
        except NatsTimeoutError:
            await logger.awarning(f"Timeout getting key `{key}` from bucket `{bucket_name}`")
            raise
        except Exception as e:
            await logger.aerror(f"Error getting key `{key}`: {str(e)}")
            return None

    async def delete_kv(
            self,
            bucket_name: str,
            key: str
    ) -> None:
        """
        Delete a key from a KV bucket.

        Args:
            bucket_name: Name of the KV bucket
            key: Key to delete
            timeout: Operation timeout in seconds

        Raises:
            NatsTimeoutError: If operation times out
            ValueError: If bucket doesn't exist or client not connected
        """
        kv = await self.get_or_create_kv_bucket(bucket_name)
        await kv.delete(key)
        await logger.adebug(f"Deleted key `{key}` from KV bucket `{bucket_name}`")


async def main():
    """Example usage of NatsClient with KV operations."""
    nats_client = NatsClient("nats://localhost:4222")

    async def example_usage():
        # Example data
        test_data = {"id": 1, "name": "test", "data": [1, 2, 3]}

        # Put value
        await nats_client.put_kv("TestBucket", "test_key", test_data)

        # # Get value
        # result = await nats_client.get_kv("TestBucket", "test_key")
        # print(f"Retrieved value: {result}")
        #
        # # Delete value
        # await nats_client.delete_kv("TestBucket", "test_key")
        #
        # # Verify deletion
        # result_after_delete = await nats_client.get_kv("TestBucket", "test_key")
        # print(f"Value after deletion: {result_after_delete}")

    try:
        async with nats_client.connection():
            await example_usage()
    except Exception as e:
        await logger.aerror(f"Error in example: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())