import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger("events")


@dataclass
class DomainEvent:
    name: str
    aggregate_id: uuid.UUID
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)


class DomainEventPublisher:
    _handlers: list[Callable[[DomainEvent], None]] = []

    @classmethod
    def register_handler(cls, handler: Callable[[DomainEvent], None]) -> None:
        cls._handlers.append(handler)

    @classmethod
    def publish(cls, name: str, aggregate_id: uuid.UUID, payload: dict[str, Any]) -> DomainEvent:
        event = DomainEvent(name=name, aggregate_id=aggregate_id, payload=payload)
        logger.info(
            "Domain event published",
            event_name=event.name,
            aggregate_id=str(event.aggregate_id),
            event_id=str(event.event_id),
        )
        for handler in cls._handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Error in domain event handler", error=str(e), event_name=event.name)
        return event
