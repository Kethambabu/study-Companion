import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.auth.jwt import hash_password
from app.modules.auth.models import Profile, Space, SpaceMember
from app.modules.auth.service import (
    _IN_MEMORY_MEMBERS,
    _IN_MEMORY_PROFILES,
    _IN_MEMORY_SPACES,
    _IN_MEMORY_USERS,
)
from app.modules.materials.models import Material
from app.modules.materials.service import _IN_MEMORY_MATERIALS
from app.modules.projects.models import Project
from app.modules.projects.service import _IN_MEMORY_PROJECTS

logger = get_logger("seed")

DEFAULT_PASSWORD = "password123"

# Seed User Definitions
DEMO_USERS = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "password": DEFAULT_PASSWORD,
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "email": "varshitha@example.com",
        "full_name": "Varshitha",
        "role": "student",
        "password": DEFAULT_PASSWORD,
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "email": "studentb@example.com",
        "full_name": "Student B",
        "role": "student",
        "password": DEFAULT_PASSWORD,
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "email": "studentc@example.com",
        "full_name": "Student C",
        "role": "student",
        "password": DEFAULT_PASSWORD,
    },
]

# Demo Spaces & Projects Scoped to Users for optional testing/seeding
DEFAULT_DEMO_SPACES = [
    # Student A (Varshitha)
    {
        "id": uuid.UUID("a1111111-1111-1111-1111-111111111111"),
        "owner_id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "name": "AI & Machine Learning",
        "slug": "ai-machine-learning",
        "description": "Learning modern AI technologies and LLM architectures.",
        "visual_metadata": {"icon": "🤖", "color_theme": "indigo", "color": "#6366f1"},
        "projects": [
            {
                "id": uuid.UUID("a1111111-2222-1111-1111-111111111111"),
                "name": "RAG Fundamentals",
                "description": "Master retrieval augmented generation, embeddings, and vector search.",
                "learning_goal": "Master vector search, embeddings, reranking, and retrieval augmented generation",
                "status": "active",
                "materials": [
                    "Vector Indexing Basics.pdf",
                    "Embedding Models Deep Dive.pdf",
                    "Chunking Strategies.pdf",
                    "Reranking & Context Construction.pdf",
                ],
            },
            {
                "id": uuid.UUID("a1111111-3333-1111-1111-111111111111"),
                "name": "LLM Fine-Tuning",
                "description": "Understand PEFT, LoRA, QLoRA, and dataset curation.",
                "learning_goal": "Understand PEFT, LoRA, QLoRA, and dataset curation",
                "status": "active",
                "materials": [
                    "LoRA Configuration Guide.pdf",
                    "SFT Dataset Curation.pdf",
                ],
            },
        ],
    },
    {
        "id": uuid.UUID("a2222222-1111-1111-1111-111111111111"),
        "owner_id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "name": "Python",
        "slug": "python",
        "description": "Core and advanced Python development techniques.",
        "visual_metadata": {"icon": "🐍", "color_theme": "emerald", "color": "#10b981"},
        "projects": [
            {
                "id": uuid.UUID("a2222222-2222-1111-1111-111111111111"),
                "name": "Advanced Python",
                "description": "Master decorators, asyncio, GIL, and metaclasses.",
                "learning_goal": "Asyncio, decorators, and meta-programming",
                "status": "active",
                "materials": [
                    "Asyncio Patterns.pdf",
                    "Decorator Masterclass.pdf",
                    "Memory Optimization in Python.pdf",
                ],
            },
        ],
    },
    # Student B
    {
        "id": uuid.UUID("b1111111-1111-1111-1111-111111111111"),
        "owner_id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "name": "Data Structures",
        "slug": "data-structures",
        "description": "Algorithmic mastery and core data structures.",
        "visual_metadata": {"icon": "⚡", "color_theme": "cyan", "color": "#3b82f6"},
        "projects": [
            {
                "id": uuid.UUID("b1111111-2222-1111-1111-111111111111"),
                "name": "DSA Interview Preparation",
                "description": "Trees, graphs, dynamic programming, and binary search.",
                "learning_goal": "Master trees, graphs, and dynamic programming for interviews",
                "status": "active",
                "materials": ["Graph Algorithms Cheat Sheet.pdf", "Dynamic Programming Patterns.pdf"],
            },
        ],
    },
    {
        "id": uuid.UUID("b2222222-1111-1111-1111-111111111111"),
        "owner_id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "name": "DBMS",
        "slug": "dbms",
        "description": "Relational database management and query tuning.",
        "visual_metadata": {"icon": "🗄️", "color_theme": "amber", "color": "#f59e0b"},
        "projects": [
            {
                "id": uuid.UUID("b2222222-2222-1111-1111-111111111111"),
                "name": "SQL Mastery",
                "description": "Advanced indexing, join optimization, and ACID transactions.",
                "learning_goal": "Advanced indexing, join optimization, and transactions",
                "status": "active",
                "materials": ["PostgreSQL Indexing Deep Dive.pdf"],
            },
        ],
    },
    # Student C
    {
        "id": uuid.UUID("c1111111-1111-1111-1111-111111111111"),
        "owner_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "name": "Cyber Security",
        "slug": "cyber-security",
        "description": "Network security, cryptography, and defense.",
        "visual_metadata": {"icon": "🛡️", "color_theme": "rose", "color": "#ef4444"},
        "projects": [
            {
                "id": uuid.UUID("c1111111-2222-1111-1111-111111111111"),
                "name": "Cryptography",
                "description": "Symmetric encryption, RSA, and modern crypto primitives.",
                "learning_goal": "Symmetric encryption, RSA, and modern crypto primitives",
                "status": "active",
                "materials": ["Public Key Infrastructure.pdf", "TLS 1.3 Architecture.pdf"],
            },
        ],
    },
    {
        "id": uuid.UUID("c2222222-1111-1111-1111-111111111111"),
        "owner_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "name": "Machine Learning",
        "slug": "machine-learning",
        "description": "Classical ML algorithms and evaluation metrics.",
        "visual_metadata": {"icon": "📊", "color_theme": "violet", "color": "#8b5cf6"},
        "projects": [
            {
                "id": uuid.UUID("c2222222-2222-1111-1111-111111111111"),
                "name": "ML Fundamentals",
                "description": "Regression, classification, decision trees, and ensemble methods.",
                "learning_goal": "Regression, classification, decision trees, and ensemble methods",
                "status": "active",
                "materials": ["Supervised Learning Essentials.pdf"],
            },
        ],
    },
]


async def seed_demo_data(db: AsyncSession | None = None, include_demo_spaces: bool = True) -> None:
    """Seeds demo users, spaces, projects, and materials in both DB and in-memory repositories."""
    from sqlalchemy import or_

    now = datetime.now(UTC)
    email_to_id: dict[str, uuid.UUID] = {}

    # Pre-fetch existing DB entities in 4 batch queries to avoid N+1 queries over remote DB
    db_profiles: dict[str, Profile] = {}
    db_spaces: dict[uuid.UUID, Space] = {}
    db_projects: dict[uuid.UUID, Project] = {}
    db_materials: dict[uuid.UUID, Material] = {}

    if db is not None:
        try:
            p_res = await db.execute(select(Profile))
            for p in p_res.scalars().all():
                db_profiles[p.email.lower().strip()] = p

            sp_res = await db.execute(select(Space))
            for sp in sp_res.scalars().all():
                db_spaces[sp.id] = sp

            pj_res = await db.execute(select(Project))
            for pj in pj_res.scalars().all():
                db_projects[pj.id] = pj

            mat_res = await db.execute(select(Material))
            for m in mat_res.scalars().all():
                db_materials[m.id] = m
        except Exception as e:
            logger.warning(f"Error pre-fetching DB seed state: {e}")
            try:
                await db.rollback()
            except Exception:
                pass

    # 1. Seed Profiles & In-Memory Users
    new_profiles = False
    for u_def in DEMO_USERS:
        u_id = u_def["id"]
        email = u_def["email"].lower().strip()
        pwd_hash = hash_password(u_def["password"])

        existing_prof = db_profiles.get(email)
        if existing_prof:
            u_id = existing_prof.id
            existing_prof.password_hash = pwd_hash
            existing_prof.full_name = u_def["full_name"]
            existing_prof.role = u_def["role"]
            profile = existing_prof
        else:
            profile = Profile(
                id=u_id,
                email=email,
                full_name=u_def["full_name"],
                password_hash=pwd_hash,
                role=u_def["role"],
                created_at=now,
                updated_at=now,
            )
            if db is not None:
                db.add(profile)
                new_profiles = True

        email_to_id[email] = u_id
        _IN_MEMORY_USERS[email] = {"user_id": u_id, "hash": pwd_hash}
        _IN_MEMORY_PROFILES[str(u_id)] = profile

    studenta_id = email_to_id.get("varshitha@example.com", uuid.UUID("22222222-2222-2222-2222-222222222222"))
    studenta_email = "studenta@example.com"
    pwd_hash = hash_password(DEFAULT_PASSWORD)
    _IN_MEMORY_USERS[studenta_email] = {"user_id": studenta_id, "hash": pwd_hash}

    if db is not None and new_profiles:
        try:
            await db.commit()
            logger.info("Successfully committed demo profiles to DB.")
        except Exception as e:
            await db.rollback()
            logger.warning(f"Could not commit demo profiles to DB: {e}")

    # 2. Seed Spaces, Members, Projects, and Materials
    spaces_to_seed = DEFAULT_DEMO_SPACES if include_demo_spaces else []
    new_entities = False
    for s_def in spaces_to_seed:
        sp_id = s_def["id"]
        original_owner = s_def["owner_id"]
        owner_id = original_owner
        if original_owner == uuid.UUID("22222222-2222-2222-2222-222222222222"):
            owner_id = email_to_id.get("varshitha@example.com", original_owner)
        elif original_owner == uuid.UUID("33333333-3333-3333-3333-333333333333"):
            owner_id = email_to_id.get("studentb@example.com", original_owner)
        elif original_owner == uuid.UUID("44444444-4444-4444-4444-444444444444"):
            owner_id = email_to_id.get("studentc@example.com", original_owner)

        space = db_spaces.get(sp_id)
        if not space:
            space = Space(
                id=sp_id,
                name=s_def["name"],
                slug=s_def["slug"],
                description=s_def["description"],
                visual_metadata=s_def["visual_metadata"],
                owner_id=owner_id,
                created_at=now,
                updated_at=now,
            )
            member = SpaceMember(
                id=uuid.uuid4(),
                space_id=sp_id,
                user_id=owner_id,
                role="owner",
                created_at=now,
            )
            if db is not None:
                db.add(space)
                db.add(member)
                new_entities = True
        else:
            member = SpaceMember(
                id=uuid.uuid4(),
                space_id=sp_id,
                user_id=owner_id,
                role="owner",
                created_at=now,
            )

        _IN_MEMORY_SPACES[str(sp_id)] = space
        _IN_MEMORY_MEMBERS[str(sp_id)] = [member]

        for p_def in s_def.get("projects", []):
            p_id = p_def["id"]
            proj = db_projects.get(p_id)
            if not proj:
                proj = Project(
                    id=p_id,
                    space_id=sp_id,
                    owner_id=owner_id,
                    title=p_def["name"],
                    name=p_def["name"],
                    description=p_def["description"],
                    learning_goal=p_def["learning_goal"],
                    status=p_def["status"],
                    created_at=now,
                    updated_at=now,
                )
                if db is not None:
                    db.add(proj)
                    new_entities = True

            _IN_MEMORY_PROJECTS[str(p_id)] = proj

            for mat_name in p_def.get("materials", []):
                m_id = uuid.uuid4()
                mat = Material(
                    id=m_id,
                    project_id=p_id,
                    owner_id=owner_id,
                    filename=mat_name,
                    content_type="application/pdf",
                    storage_path=f"demo/{owner_id}/{p_id}/{mat_name}",
                    file_size=1024 * 150,
                    file_size_bytes=1024 * 150,
                    checksum=f"demo_checksum_{m_id}",
                    status="ready",
                    created_at=now,
                    updated_at=now,
                )
                _IN_MEMORY_MATERIALS[str(m_id)] = mat

    if db is not None and new_entities:
        try:
            await db.commit()
            logger.info("Database successfully committed seed demo spaces & projects.")
        except Exception as e:
            await db.rollback()
            logger.warning(f"Could not commit seed spaces/projects to DB: {e}")

    logger.info("Demo data seeding completed for Admin, Varshitha, Student B, and Student C.")
