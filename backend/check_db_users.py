import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.auth.models import Profile

async def check_users():
    async with AsyncSessionLocal() as session:
        stmt = select(Profile)
        res = await session.execute(stmt)
        profiles = res.scalars().all()
        print("CURRENT PROFILES IN DB:")
        for p in profiles:
            print(f"- ID: {p.id}, Email: {p.email}, Role: {p.role}, Name: {p.full_name}")

if __name__ == "__main__":
    asyncio.run(check_users())
