import asyncio
import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    admin_email = "admin@example.com"
    admin_password = "Admin123!"
    admin_hash = pwd_context.hash(admin_password)

    # Try standard 5432 and pooler 6543
    hosts = ["db.eirqfwcyvctqvukzuiol.supabase.co"]
    ports = [5432, 6543]
    
    conn = None
    for host in hosts:
        for port in ports:
            print(f"Trying to connect to {host}:{port}...")
            try:
                conn = await asyncio.wait_for(
                    asyncpg.connect(
                        user="postgres",
                        password="ketham@babu",
                        database="postgres",
                        host=host,
                        port=port,
                        timeout=10,
                    ),
                    timeout=12
                )
                print(f"Connected successfully to {host}:{port}!")
                break
            except Exception as e:
                print(f"Failed to connect to {host}:{port}: {e}")
        if conn:
            break
            
    if not conn:
        print("Could not connect to Supabase DB directly. Please check network/DB pooler availability.")
        return

    try:
        # Delete non-admin profiles
        res = await conn.execute("DELETE FROM public.profiles WHERE lower(email) != $1;", admin_email)
        print(f"Deleted non-admin rows: {res}")
        
        # Check if admin profile exists
        row = await conn.fetchrow("SELECT id FROM public.profiles WHERE lower(email) = $1;", admin_email)
        if row:
            await conn.execute(
                "UPDATE public.profiles SET password_hash = $1, role = 'admin', full_name = 'Platform Administrator' WHERE lower(email) = $2;",
                admin_hash, admin_email
            )
            print(f"Updated admin profile for {admin_email}.")
        else:
            await conn.execute(
                "INSERT INTO public.profiles (id, email, full_name, password_hash, role) VALUES ('701acef0-1ed6-4974-b31c-059d38989899', $1, 'Platform Administrator', $2, 'admin');",
                admin_email, admin_hash
            )
            print(f"Inserted admin profile for {admin_email}.")
            
        profiles = await conn.fetch("SELECT id, email, full_name, role FROM public.profiles;")
        print("REMAINING PROFILES IN DATABASE:")
        for p in profiles:
            print(f"- {p['email']} | {p['full_name']} | {p['role']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
