import asyncio
import sys
import uuid
from sqlalchemy import delete, select

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.auth.models import Profile, SpaceMember, Space
from app.modules.auth.jwt import hash_password

async def clean_credentials():
    admin_email = "admin@example.com"
    admin_password = "Admin123!"
    admin_hash = hash_password(admin_password)

    async with AsyncSessionLocal() as session:
        print("Cleaning up database credentials...")
        
        # 1. Fetch all profiles
        stmt = select(Profile)
        res = await session.execute(stmt)
        profiles = res.scalars().all()
        
        admin_profile = None
        for p in profiles:
            if p.email.lower() == admin_email:
                admin_profile = p
            else:
                print(f"Deleting non-admin user profile: {p.email}")
                await session.delete(p)

        # 2. Ensure admin@example.com profile exists and is updated
        if admin_profile:
            print(f"Updating admin user profile ({admin_email})...")
            admin_profile.password_hash = admin_hash
            admin_profile.role = "admin"
            admin_profile.full_name = "Platform Administrator"
        else:
            print(f"Creating seed admin user profile ({admin_email})...")
            admin_profile = Profile(
                id=uuid.UUID("701acef0-1ed6-4974-b31c-059d38989899"),
                email=admin_email,
                full_name="Platform Administrator",
                password_hash=admin_hash,
                role="admin",
            )
            session.add(admin_profile)

        await session.commit()
        print("Database cleanup complete! Only admin@example.com remains.")

if __name__ == "__main__":
    asyncio.run(clean_credentials())
