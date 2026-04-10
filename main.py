import os
from urllib.parse import quote_plus

def get_database_url() -> str:
    # Use DATABASE_URL if Replit provides it
    direct = os.getenv("DATABASE_URL")
    if direct:
        return direct

    # Otherwise build it from PG* variables
    required = ["PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing database env vars: {', '.join(missing)}")

    host = os.environ["PGHOST"]
    port = os.environ["PGPORT"]
    user = os.environ["PGUSER"]
    password = quote_plus(os.environ["PGPASSWORD"])
    database = os.environ["PGDATABASE"]

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def require_object_storage_bucket() -> str:
    bucket = os.getenv("OBJECT_STORAGE_BUCKET")
    if not bucket:
        raise RuntimeError("Missing OBJECT_STORAGE_BUCKET")
    return bucket

if __name__ == "__main__":
    db_url = get_database_url()
    bucket = require_object_storage_bucket()

    print("DB: OK")
    print("Bucket:", bucket)