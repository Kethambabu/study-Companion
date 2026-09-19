import asyncio
import uuid
import sys

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import SignupRequest, LoginRequest
from app.modules.projects.service import ProjectsService

async def test_student_lifecycle():
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        
        test_email = f"student_test_{uuid.uuid4().hex[:6]}@example.com"
        test_password = "Password123!"
        test_name = "Student Test User"
        
        print(f"1. Testing Signup for {test_email}...")
        try:
            signup_res = await auth_service.signup(
                SignupRequest(email=test_email, password=test_password, full_name=test_name)
            )
            print(f"Signup successful! User ID: {signup_res.user.id}")
        except Exception as e:
            print(f"Signup FAILED: {e}")
            return
            
        print("2. Testing Login...")
        try:
            login_res = await auth_service.login(
                LoginRequest(email=test_email, password=test_password)
            )
            print(f"Login successful! Role: {login_res.user.role}")
        except Exception as e:
            print(f"Login FAILED: {e}")
            return

        print("3. Testing List Spaces...")
        try:
            spaces = await auth_service.list_user_spaces(login_res.user.id)
            print(f"Spaces retrieved successfully! Count: {len(spaces)}")
            for sp in spaces:
                print(f"  - Space: {sp.name} (id: {sp.id})")
        except Exception as e:
            print(f"List Spaces FAILED: {e}")
            return

        print("4. Testing List Projects...")
        try:
            projects_service = ProjectsService(db)
            projects_res = await projects_service.list_projects(login_res.user.id)
            print(f"Projects retrieved successfully! Count: {len(projects_res.items)}")
        except Exception as e:
            import traceback
            print(f"List Projects FAILED: {e}")
            traceback.print_exc()
            return

        print("ALL STUDENT FLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_student_lifecycle())
