import asyncio
from functools import partial
from typing import Callable, Awaitable, Optional

import ormsgpack
import structlog
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.js.api import ConsumerConfig, AckPolicy, DeliverPolicy
from nats.js import JetStreamContext
from nats.errors import TimeoutError as NATSTimeoutError

from src.infrastructure.logger.loggers import InitLoggers

logger: structlog.BoundLogger = structlog.getLogger(InitLoggers.main.name)


class NATSClient:
    """
    Asynchronous NATS JetStream client wrapper with persistent pull-subscription support.
    """

    def __init__(self, servers: Optional[list[str]] = None) -> None:
        """
        Initialize NATSClient with optional list of servers.

        Args:
            servers (Optional[list[str]]): NATS server URLs.
        """
        self.servers = servers or ["nats://127.0.0.1:4222"]
        self.nc: NATS = NATS()
        self.js: Optional[JetStreamContext] = None
        self.tasks: list[asyncio.Task] = []

    async def connect(self) -> None:
        """
        Connect to NATS and initialize JetStream context.

        Raises:
            Exception: If connection to NATS fails.
        """
        try:
            await self.nc.connect(servers=self.servers)
            self.js = self.nc.jetstream()
            await logger.ainfo("Connected to NATS JetStream", servers=self.servers)
        except Exception as e:
            await logger.aerror("Failed to connect to NATS", error=str(e))
            raise

    async def disconnect(self) -> None:
        """
        Gracefully cancel background tasks and disconnect from NATS.
        """
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        await self.nc.close()
        await logger.ainfo("Disconnected from NATS")

    async def create_stream(self, name: str, subjects: list[str]) -> None:
        """
        Create a NATS JetStream stream if it doesn't exist.

        Args:
            name (str): Stream name.
            subjects (list[str]): Subjects to bind to the stream.
        """
        try:
            await self.js.stream_info(name)
            await logger.ainfo("Stream already exists", stream=name)
        except Exception:
            await self.js.add_stream(name=name, subjects=subjects)
            await logger.ainfo("Stream created", stream=name, subjects=subjects)

    async def add_subscription(
        self,
        subject: str,
        durable_name: str,
        callback,
        ack_wait_seconds: int = 10,
    ) -> None:
        """
        Add a pull-based JetStream subscription with a background processor.

        Args:
            subject (str): Subject to subscribe to.
            durable_name (str): Durable consumer name.
            callback (Callable[[Msg], Awaitable[None]]): Async message callback.
            ack_wait_seconds (int): Time to wait for ack before redelivery.
        """
        config = ConsumerConfig(
            durable_name=durable_name,
            ack_policy=AckPolicy.EXPLICIT,
            ack_wait=ack_wait_seconds,
            deliver_policy=DeliverPolicy.ALL,
        )

        pull_sub: JetStreamContext.PullSubscription = await self.js.pull_subscribe(
            subject=subject,
            durable=durable_name,
            config=config,
        )

        task = asyncio.create_task(self._process_messages(pull_sub, callback))
        self.tasks.append(task)

    async def _process_messages(
        self, pull_sub: JetStreamContext.PullSubscription, callback: Callable[[Msg], Awaitable[None]]
    ) -> None:
        """
        Internal background task to pull and process messages.

        Args:
            pull_sub (PullSubscription): JetStream pull-subscription.
            callback (Callable[[Msg], Awaitable[None]]): Message processing function.
        """
        try:
            while True:
                try:
                    msgs = await pull_sub.fetch(1, timeout=5)
                    for msg in msgs:
                        await callback(msg)
                except NATSTimeoutError:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            await logger.adebug("Subscription cancelled", info=pull_sub.consumer_info())
        finally:
            await pull_sub.unsubscribe()

    async def publish(self, subject: str, message: dict) -> None:
        """
        Publish a message to a subject using JetStream.

        Args:
            subject (str): Target subject.
            message (dict): JSON-serializable message content.

        Raises:
            Exception: On serialization or publishing failure.
        """
        try:
            await logger.adebug("Publishing message", subject=subject, message=message)
            data = ormsgpack.packb(message)
            await self.js.publish(subject, data)
        except Exception as e:
            await logger.aerror("Failed to publish message", subject=subject, error=str(e))
            raise


async def main() -> None:
    client = NATSClient(servers=["nats://localhost:4222"])
    await client.connect()

    async def example_callback(msg: Msg, x: int) -> None:
        """
        Example message processing function.

        Args:
            msg (Msg): Incoming NATS message.
            x (int): Example external value.
        """
        await asyncio.sleep(5)
        data = ormsgpack.unpackb(msg.data)
        print(f"Received: {data}, x={x}")
        await msg.ack()

    try:
        await client.create_stream(name="TestStream", subjects=["TestSubject"])

        cb = partial(example_callback, x=5)
        await client.add_subscription(
            subject="TestSubject",
            durable_name="TestSubjectConsumer",
            callback=cb,
            ack_wait_seconds=10,
        )

        for i in range(10):
            await client.publish(
                "TestSubject",
                {"text": f"Hello World {i + 1}!", "result": False},
            )

        await asyncio.Event().wait()

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
