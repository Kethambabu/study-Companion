import asyncio
import sys
import uuid
import traceback

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import SignupRequest
from app.modules.auth.models import Profile, Space, SpaceMember

async def test_db_insert():
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    print(f"Testing direct DB signup for {email}...")

    async with AsyncSessionLocal() as session:
        try:
            auth_service = AuthService(session)
            res = await auth_service.signup(SignupRequest(
                email=email,
                password="TestPassword123!",
                full_name="Test Signup User"
            ))
            print("Signup returned token response!")

            # Verify if user is actually in database session
            from sqlalchemy import select
            stmt = select(Profile).where(Profile.email == email)
            result = await session.execute(stmt)
            p = result.scalar_one_or_none()
            if p:
                print(f"SUCCESS! Profile found in database with ID: {p.id}")
            else:
                print("FAILURE! Profile was NOT found in database after signup!")
        except Exception as e:
            print(f"EXPLICIT ERROR DURING SIGNUP: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_insert())
