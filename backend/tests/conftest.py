import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://nearby:nearby@localhost:5432/nearby")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_PUBLIC_PER_MIN", "10000")
os.environ.setdefault("RATE_LIMIT_SEARCH_PER_MIN", "10000")
os.environ.setdefault("RATE_LIMIT_LOGIN_PER_MIN", "10000")
os.environ.setdefault("SEED_SAMPLE_DATA", "false")
os.environ.setdefault("ADMIN_EMAIL", "admin@nearby.local")
os.environ.setdefault("ADMIN_PASSWORD", "ChangeMe123!")
