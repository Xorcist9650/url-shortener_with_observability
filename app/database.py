import time
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=10,
    decode_responses=True,
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    r = redis.Redis(connection_pool = redis_pool)
    try:
        yield r
    finally:
        pass

def init_db(retries: int=5, delay: int=5):
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception:
            if attempt == retries-1:
                raise
            time.sleep(delay)
