import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Fetch database credentials from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "community_db")

# Construct SQLAlchemy database URL (defaults to postgresql+pg8000/psycopg2)
# Using standard pg8000 or psycopg2-binary driver
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Connect to database with connection pooling configuration
# AlloyDB / PostgreSQL benefits from pooling in production; SQLite does not support these parameters
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True
    )

# Create local session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Dependency for FastAPI endpoints to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
