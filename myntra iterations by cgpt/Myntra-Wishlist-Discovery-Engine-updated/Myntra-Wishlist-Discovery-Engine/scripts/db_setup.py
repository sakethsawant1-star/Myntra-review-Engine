import os
import psycopg2

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise SystemExit("DATABASE_URL is not set. Export it or add it to a local .env file.")

print(f"Connecting to database...")

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # 1. Run all migrations in order. Each migration is idempotent.
    migrations_dir = os.path.join("database", "migrations")
    for filename in sorted(name for name in os.listdir(migrations_dir) if name.endswith(".sql")):
        migration_path = os.path.join(migrations_dir, filename)
        print(f"Executing migration: {migration_path}")
        with open(migration_path, "r", encoding="utf-8") as f:
            cursor.execute(f.read())
    print("Migrations successful.")

    # 2. Seed only an empty database; this makes setup safe to re-run.
    cursor.execute("SELECT COUNT(*) FROM raw_evidence")
    if cursor.fetchone()[0] == 0:
        seed_path = os.path.join("database", "seed", "seed_evidence.sql")
        print(f"Executing seed: {seed_path}")
        with open(seed_path, "r", encoding="utf-8") as f:
            cursor.execute(f.read())
        print("Seed successful.")
    else:
        print("Seed skipped; raw_evidence already contains data.")
    
    cursor.close()
    conn.close()
    print("Database setup complete!")

except Exception as e:
    raise SystemExit("Database setup failed. Check DATABASE_URL and the migration files.") from e
