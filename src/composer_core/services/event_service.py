import asyncio
from collections import defaultdict
from typing import Dict, AsyncGenerator

class LiveEventService:
    """
    A service for publishing and subscribing to live, task-specific events.
    This uses a simple in-memory pub/sub model. For a production system,
    this might be replaced with a more robust message queue like Redis Pub/Sub.
    """
    def __init__(self):
        self._subscribers: Dict[str, list] = defaultdict(list)

    async def publish(self, task_id: str, message: str):
        """Publish a message to all subscribers of a given task_id."""
        for queue in self._subscribers.get(task_id, []):
            await queue.put(message)

    async def subscribe(self, task_id: str) -> AsyncGenerator[str, None]:
        """Subscribe to messages for a given task_id."""
        queue = asyncio.Queue()
        self._subscribers[task_id].append(queue)
        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            self._subscribers[task_id].remove(queue)

# Singleton instance of the event service
event_service = LiveEventService() 