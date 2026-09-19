import asyncio
import sys
import uuid

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.auth.models import Profile, Space, SpaceMember
from app.modules.auth.jwt import hash_password
from sqlalchemy import select

async def test_persistent_signup():
    email = f"real_student_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "StudentPassword123!"
    pwd_hash = hash_password(pwd)
    user_id = uuid.uuid4()
    
    print(f"Creating real user {email} in Supabase DB...")
    async with AsyncSessionLocal() as db:
        profile = Profile(
            id=user_id,
            email=email,
            full_name="Real Student",
            password_hash=pwd_hash,
            role="user",
        )
        space_id = uuid.uuid4()
        space = Space(
            id=space_id,
            name="Real Student's Space",
            slug=f"space-{user_id.hex[:6]}",
            owner_id=user_id,
        )
        member = SpaceMember(
            id=uuid.uuid4(),
            space_id=space_id,
            user_id=user_id,
            role="owner",
        )
        db.add(profile)
        db.add(space)
        db.add(member)
        
        await db.commit()
        print("COMMIT SUCCEEDED!")

    # Verify user exists in fresh session
    async with AsyncSessionLocal() as fresh_db:
        stmt = select(Profile).where(Profile.email == email)
        res = await fresh_db.execute(stmt)
        found = res.scalar_one_or_none()
        if found:
            print(f"VERIFIED: User {email} is in Supabase DB with ID {found.id}!")
        else:
            print("FAILED: User not found in DB!")

if __name__ == "__main__":
    asyncio.run(test_persistent_signup())
