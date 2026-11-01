# backend/migrate_neon_to_azure.py
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# -----------------------------
# CONNECTION STRINGS
# -----------------------------
NEON_URL = "postgresql+psycopg2://neondb_owner:npg_fJPwHc04DCTq@ep-muddy-boat-a89g7xku-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
AZURE_URL = "postgresql+psycopg2://tejas:group8_cloud@docchain-08.postgres.database.azure.com:5432/postgres?sslmode=require"

# -----------------------------
# ENGINES & SESSIONS
# -----------------------------
src_engine = create_engine(NEON_URL)
dst_engine = create_engine(AZURE_URL)

src_meta = MetaData()
src_meta.reflect(bind=src_engine)

# Recreate tables in Azure (if needed)
print("Creating schema in Azure...")
src_meta.create_all(bind=dst_engine)

src_session = sessionmaker(bind=src_engine)()
dst_session = sessionmaker(bind=dst_engine)()

# -----------------------------
# DATA MIGRATION
# -----------------------------
for table in tqdm(src_meta.sorted_tables, desc="Migrating tables"):
    rows = src_session.execute(table.select()).fetchall()
    if rows:
        print(f"Inserting {len(rows)} rows into {table.name}...")
        # Convert Row objects to dicts
        data = [dict(r._mapping) for r in rows]
        dst_session.execute(table.insert(), data)
        dst_session.commit()

print("✅ Migration complete!")
src_session.close()
dst_session.close()
