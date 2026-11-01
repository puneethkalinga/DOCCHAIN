import os
from sqlalchemy import create_engine, text

# Neon Cloud Database URL
DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_EiLCHofW60TI@ep-shy-flower-awl3bp43.c-12.us-east-1.aws.neon.tech/docchain_db?sslmode=require"

print("="*60)
print(" CONNECTING TO CLOUD DATABASE (NEON POSTGRESQL)...")
print("="*60)

try:
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require", "connect_timeout": 10})
    with engine.connect() as conn:
        print("\n[TABLE 1: USERS]")
        users = conn.execute(text("SELECT id, email, role, is_active, upload_enabled, created_at FROM users;")).fetchall()
        for u in users:
            print(f" • ID: {u[0]} | Email: {u[1]} | Role: {u[2]} | Active: {u[3]} | Upload: {u[4]}")

        print("\n[TABLE 2: LETTERS / DOCUMENTS]")
        letters = conn.execute(text("SELECT id, file_name_original, status, sha256, created_at FROM letters;")).fetchall()
        if not letters:
            print(" (No letters uploaded yet)")
        for l in letters:
            print(f" • ID: {l[0]} | File: {l[1]} | Status: {l[2]} | SHA256: {l[3][:16]}...")

        print("\n[TABLE 3: ACCESS LOGS / AUDIT TRAIL]")
        logs = conn.execute(text("SELECT id, action, ip, ts FROM access_logs;")).fetchall()
        if not logs:
            print(" (No access logs recorded yet)")
        for log in logs:
            print(f" • ID: {log[0]} | Action: {log[1]} | IP: {log[2]} | Time: {log[3]}")

    print("\n" + "="*60)
    print(" [OK] Database queried successfully.")
    print("="*60)
except Exception as e:
    print("\n[Error connecting to Neon PostgreSQL]:", e)
    print("Checking local fallback SQLite database (docchain.db)...")
    import sqlite3
    conn = sqlite3.connect("docchain.db")
    c = conn.cursor()
    print("\n[LOCAL TABLE: USERS]")
    for r in c.execute("SELECT id, email, role, is_active FROM users;"):
        print(f" • ID: {r[0]} | Email: {r[1]} | Role: {r[2]} | Active: {r[3]}")
    conn.close()
