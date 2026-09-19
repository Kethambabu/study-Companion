import sys
import argparse
import asyncio
from sqlalchemy import select

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.auth.models import Profile
from app.modules.auth.jwt import hash_password

async def reset_user_password(email: str, new_password: str):
    email_clean = email.lower().strip()
    async with AsyncSessionLocal() as session:
        stmt = select(Profile).where(Profile.email == email_clean)
        res = await session.execute(stmt)
        profile = res.scalar_one_or_none()
        
        if not profile:
            print(f"Error: User with email '{email_clean}' was not found in the database.")
            return False
            
        profile.password_hash = hash_password(new_password)
        await session.commit()
        print(f"Successfully updated password for user: {email_clean}")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset a user's password in the database.")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", required=True, help="New password")
    args = parser.parse_args()
    
    asyncio.run(reset_user_password(args.email, args.password))
