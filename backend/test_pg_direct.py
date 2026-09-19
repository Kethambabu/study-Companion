import urllib.parse
import psycopg2

db_url = "postgresql://postgres:ketham%40babu@db.eirqfwcyvctqvukzuiol.supabase.co:5432/postgres"

try:
    print("Connecting via psycopg2...")
    conn = psycopg2.connect(db_url, connect_timeout=10)
    cursor = conn.cursor()
    
    # 1. Update admin@example.com password and role
    import passlib.context
    pwd_context = passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")
    admin_hash = pwd_context.hash("Admin123!")
    
    # Delete non-admin profiles
    cursor.execute("DELETE FROM public.profiles WHERE email != 'admin@example.com';")
    print(f"Deleted non-admin rows. Rows affected: {cursor.rowcount}")
    
    # Ensure admin@example.com exists
    cursor.execute("SELECT id FROM public.profiles WHERE email = 'admin@example.com';")
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE public.profiles SET password_hash = %s, role = 'admin', full_name = 'Platform Administrator' WHERE email = 'admin@example.com';",
            (admin_hash,)
        )
        print("Updated admin@example.com credentials.")
    else:
        cursor.execute(
            "INSERT INTO public.profiles (id, email, full_name, password_hash, role) VALUES ('701acef0-1ed6-4974-b31c-059d38989899', 'admin@example.com', 'Platform Administrator', %s, 'admin');",
            (admin_hash,)
        )
        print("Inserted admin@example.com profile.")
        
    conn.commit()
    cursor.close()
    conn.close()
    print("SUCCESS! Only admin@example.com remains in database.")
except Exception as e:
    print(f"Error: {e}")
