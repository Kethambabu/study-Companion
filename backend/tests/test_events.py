import uuid

from app.modules.events.publisher import DomainEvent, DomainEventPublisher


def test_domain_event_publishing():
    received_events: list[DomainEvent] = []

    def sample_handler(event: DomainEvent):
        received_events.append(event)

    DomainEventPublisher.register_handler(sample_handler)

    test_id = uuid.uuid4()
    published = DomainEventPublisher.publish(
        name="project_created",
        aggregate_id=test_id,
        payload={"project_id": str(test_id), "name": "Event Test Project"},
    )

    assert published.name == "project_created"
    assert published.aggregate_id == test_id
    assert published.payload["name"] == "Event Test Project"
    assert len(received_events) >= 1
    assert any(e.aggregate_id == test_id for e in received_events)
