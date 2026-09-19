import asyncio
import sys
import uuid
from datetime import UTC, datetime

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.tutor.models import ConversationMessage, Conversation

async def debug_commit():
    async with AsyncSessionLocal() as session:
        # Get a conversation ID
        from sqlalchemy import select
        res = await session.execute(select(Conversation).limit(1))
        conv = res.scalar_one_or_none()
        if not conv:
            print("No conversation found in DB!")
            return

        print(f"Found conversation: {conv.id}")

        asst_msg = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            sender="assistant",
            content="Debug test answer",
            citations=[{"citation_id": "[1]", "document_title": "Test.pdf", "page_number": 1}],
            metadata_json={"confidence_status": "grounded", "request_id": "test-req", "suggested_followups": ["Test followup"]},
            created_at=datetime.now(UTC),
        )

        try:
            session.add(asst_msg)
            await session.commit()
            print("Assistant message committed successfully!")
        except Exception as e:
            import traceback
            print("FAILED TO COMMIT ASSISTANT MESSAGE:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_commit())
