# Production Deployment Guide (Vercel, Render, Supabase & Redis)

## Overview

AI Prof is architected for simple cloud deployment using modern serverless and managed cloud infrastructure:
- **Frontend**: Vercel
- **Backend API & Workers**: Render
- **Database, Auth & Storage**: Supabase (PostgreSQL)
- **Redis**: Managed Redis (Render Redis / Upstash)

---

## 1. Supabase Setup (Database & Storage)

1. Create a new project in [Supabase](https://supabase.com).
2. Copy the PostgreSQL Connection String (`postgresql+asyncpg://...`).
3. Run database migration scripts or initialization tables.
4. Copy `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`.

---

## 2. Render Setup (Backend API & Worker)

1. Connect your GitHub repository to [Render](https://render.com).
2. Create a **Web Service** for the FastAPI backend:
   - **Environment**: Python 3.12+
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables:
   - `ENVIRONMENT=production`
   - `DATABASE_URL=postgresql+asyncpg://...`
   - `GROQ_API_KEY=gsk_...`
   - `GEMINI_API_KEY=AIzaSy...`
   - `SECRET_KEY=your-secure-secret-key`
   - `CORS_ORIGINS=["https://your-app.vercel.app"]`
4. Create a **Background Worker** or **Redis Instance** on Render for queue processing.

---

## 3. Vercel Setup (Frontend SPA)

1. Connect your repository to [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Set Build Command to `npm run build` and Output Directory to `dist`.
4. Add Environment Variable:
   - `VITE_API_BASE_URL=https://your-render-backend.onrender.com/api/v1`
5. Deploy.
