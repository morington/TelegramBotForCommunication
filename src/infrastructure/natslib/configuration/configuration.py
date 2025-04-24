import asyncio
from asyncio import Task
from typing import Optional, Callable, Any

import ormsgpack
import structlog
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, AckPolicy, DeliverPolicy

from ..client import NatsClient

logger = structlog.getLogger("NATS")


class ConfigurationWatcher:
    """Watches for configuration changes in a NATS KV bucket."""

    def __init__(self, nats_client: NatsClient) -> None:
        """
        Initialize configuration watcher with NATS client.

        Args:
            nats_client: Initialized NATS client instance
        """
        self._nats_client = nats_client
        self._watch_task: Optional[Task[Any]] = None

    async def set_watching(
            self,
            bucket_name: str,
            callback: Callable[[Msg], Any]
    ) -> None:
        """
        Start watching configuration changes in specified bucket.

        Args:
            bucket_name: Name of the KV bucket to watch
            callback: Async callback function to process messages

        Raises:
            ValueError: If NATS client is not connected
        """
        if not self._nats_client.is_connected:
            raise ValueError("NATS client must be connected before watching")

        subject = f"$KV.{bucket_name}.>"
        consumer_config = ConsumerConfig(
            durable_name=f"{bucket_name}_watcher",
            ack_policy=AckPolicy.EXPLICIT,
            deliver_policy=DeliverPolicy.ALL,
        )

        sub = await self._nats_client.jetstream.subscribe(
            subject=subject,
            durable=f"{bucket_name}_watcher",
            config=consumer_config
        )

        async def watch_loop():
            try:
                async for msg in sub.messages:
                    await callback(msg)
            except asyncio.CancelledError:
                await sub.unsubscribe()
                raise
            except Exception as e:
                await logger.aerror(f"Error in watch loop: {str(e)}")
                raise

        self._watch_task = asyncio.create_task(watch_loop())
        await logger.ainfo(
            f"Started watching configuration bucket `{bucket_name}`",
            callback=callback.__name__
        )

    async def stop_watching(self) -> None:
        """Stop watching configuration changes and clean up resources."""
        if self._watch_task is None:
            return

        await logger.ainfo("Stopping configuration watcher...")
        self._watch_task.cancel()
        try:
            await self._watch_task
        except asyncio.CancelledError:
            pass
        self._watch_task = None
        await logger.ainfo("Configuration watcher stopped")


async def main():
    """Example usage of NATS client and configuration watcher."""
    nats_client = NatsClient("nats://localhost:4222")
    config_watcher = ConfigurationWatcher(nats_client)

    async def example_callback(msg: Msg) -> None:
        """Example callback for processing configuration messages."""
        data = ormsgpack.unpackb(msg.data)
        print(f"Received configuration update: {data}")
        await msg.ack()

    try:
        async with nats_client.connection():
            await config_watcher.set_watching("TestBucket", example_callback)
            await asyncio.Event().wait()  # Keep running until interrupted
    finally:
        await config_watcher.stop_watching()


if __name__ == "__main__":
    asyncio.run(main())



