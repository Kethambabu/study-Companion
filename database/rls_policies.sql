-- AI Study Companion Phase 1 PostgreSQL Row-Level Security (RLS) Policies

-- ENABLE RLS ON ALL TABLES
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.spaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.space_members ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------
-- 1. PROFILES POLICIES
-- ----------------------------------------------------
-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id);

-- System service role / auth hook can insert profiles on signup
CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ----------------------------------------------------
-- 2. SPACES POLICIES
-- ----------------------------------------------------
-- Members can view spaces they belong to
CREATE POLICY "Members can view their spaces"
    ON public.spaces
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.space_members sm
            WHERE sm.space_id = public.spaces.id
              AND sm.user_id = auth.uid()
        )
    );

-- Owners can update their space
CREATE POLICY "Space owners can update their space"
    ON public.spaces
    FOR UPDATE
    USING (owner_id = auth.uid());

-- Owners can delete their space
CREATE POLICY "Space owners can delete their space"
    ON public.spaces
    FOR DELETE
    USING (owner_id = auth.uid());

-- Authenticated users can create a space
CREATE POLICY "Authenticated users can create space"
    ON public.spaces
    FOR INSERT
    WITH CHECK (owner_id = auth.uid());

-- ----------------------------------------------------
-- 3. SPACE MEMBERS POLICIES
-- ----------------------------------------------------
-- Members can view membership list of spaces they belong to
CREATE POLICY "Members can view space members"
    ON public.space_members
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.space_members sm
            WHERE sm.space_id = public.space_members.space_id
              AND sm.user_id = auth.uid()
        )
    );

-- Admins and owners can insert/update/delete members
CREATE POLICY "Admins can manage space members"
    ON public.space_members
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.space_members sm
            WHERE sm.space_id = public.space_members.space_id
              AND sm.user_id = auth.uid()
              AND sm.role IN ('owner', 'admin')
        )
    );
