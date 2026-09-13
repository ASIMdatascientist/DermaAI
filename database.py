from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ===============================
# DATABASE URL
# ===============================

DATABASE_URL = "sqlite:///./database.db"


# ===============================
# DATABASE ENGINE
# ===============================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# ===============================
# DATABASE SESSION
# ===============================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ===============================
# BASE
# ===============================

Base = declarative_base()


# ===============================
# DB DEPENDENCY (used in FastAPI routes)
# ===============================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()