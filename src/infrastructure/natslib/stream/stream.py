import asyncio
from typing import Optional, Callable, Any, Awaitable, Dict
from functools import partial

import ormsgpack
import structlog
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, AckPolicy, DeliverPolicy
from nats.errors import TimeoutError as NATSTimeoutError

from ..client import NatsClient

logger = structlog.getLogger("NATS")


class SubscriptionWrapper:
    """Wraps subscription-related data."""
    def __init__(self, task: asyncio.Task, pull_sub) -> None:
        self.task = task
        self.pull_sub = pull_sub


class StreamClient:
    """Manages multiple NATS JetStream subscriptions."""

    def __init__(self, nats_client: NatsClient) -> None:
        """
        Initialize StreamClient with a NATS client.

        Args:
            nats_client: Initialized NATS client
        """
        self._nats_client = nats_client
        self._watch_tasks: Dict[str, asyncio.Task] = {}
        self._subscriptions: Dict[str, SubscriptionWrapper] = {}
        self._callback: Optional[Callable[[Msg], Awaitable[None]]] = None
        self._ack_wait_seconds: int = 10

    async def _watch_subject(self, subject: str, durable_name: str) -> None:
        """Internal method to watch messages from a single subject."""
        consumer_config = ConsumerConfig(
            durable_name=durable_name,
            ack_policy=AckPolicy.EXPLICIT,
            deliver_policy=DeliverPolicy.ALL,
            ack_wait=self._ack_wait_seconds,
        )

        pull_sub = await self._nats_client.jetstream.pull_subscribe(
            subject=subject,
            durable=durable_name,
            config=consumer_config,
        )

        async def watch_loop():
            try:
                while True:
                    try:
                        msgs = await pull_sub.fetch(1, timeout=5)
                        for msg in msgs:
                            await self._callback(msg)
                    except NATSTimeoutError:
                        await asyncio.sleep(1)
            except asyncio.CancelledError:
                await pull_sub.unsubscribe()
                raise
            except Exception as e:
                await logger.aerror("Error in watch loop", subject=subject, error=str(e))
                raise

        task = asyncio.create_task(watch_loop())
        self._subscriptions[subject] = SubscriptionWrapper(task=task, pull_sub=pull_sub)
        await logger.ainfo("Started watching subject", subject=subject)

    async def update_subjects(
        self,
        subjects: list[str],
        callback: Callable[[Msg], Awaitable[None]],
        ack_wait_seconds: int = 10
    ) -> None:
        """
        Update the list of subjects to watch. Stops old and starts new ones.

        Args:
            subjects: List of subjects to subscribe to
            callback: Async callback for handling messages
            ack_wait_seconds: Ack wait in seconds
        """
        if not self._nats_client.is_connected:
            raise ValueError("NATS client must be connected before watching")

        self._callback = callback
        self._ack_wait_seconds = ack_wait_seconds

        old_subjects = set(self._subscriptions.keys())
        new_subjects = set(subjects)

        to_add = new_subjects - old_subjects
        to_remove = old_subjects - new_subjects

        for subject in to_remove:
            wrapper = self._subscriptions.pop(subject)
            wrapper.task.cancel()
            try:
                await wrapper.task
            except asyncio.CancelledError:
                pass
            await logger.ainfo("Stopped watching subject", subject=subject)

        for subject in to_add:
            await self._watch_subject(subject, durable_name=f"{subject}_consumer")

    async def create_stream(self, name: str, subjects: list[str]) -> None:
        """
        Create a NATS JetStream stream if not exists.

        Args:
            name: Stream name
            subjects: List of subjects
        """
        jetstream = self._nats_client.jetstream
        try:
            await jetstream.stream_info(name)
            await logger.ainfo("Stream already exists", stream=name)
        except Exception:
            await jetstream.add_stream(name=name, subjects=subjects)
            await logger.ainfo("Stream created", stream=name, subjects=subjects)

    async def publish(self, subject: str, message: dict) -> None:
        """
        Publish message via JetStream.

        Args:
            subject: Target subject
            message: Serializable message
        """
        try:
            await logger.adebug("Publishing message", subject=subject, message=message)
            data = ormsgpack.packb(message)
            await self._nats_client.jetstream.publish(subject, data)
        except Exception as e:
            await logger.aerror("Failed to publish message", subject=subject, error=str(e))
            raise

    async def stop_all(self) -> None:
        """Stop all watchers and clean resources."""
        for subject, wrapper in self._subscriptions.items():
            wrapper.task.cancel()
            try:
                await wrapper.task
            except asyncio.CancelledError:
                pass
            await logger.ainfo("Stopped watching subject", subject=subject)

        self._subscriptions.clear()
