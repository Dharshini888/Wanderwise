import os
import logging
import socket
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Search candidate .env paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
project_root = os.path.abspath(os.path.join(backend_root, ".."))

env_candidates = [
    os.path.join(backend_root, ".env"),
    os.path.join(project_root, ".env"),
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), "backend", ".env"),
]
for env_path in env_candidates:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)


def _is_service_reachable(url_str: str, default_port: int = 5432, timeout: float = 0.5) -> bool:
    """Fast non-blocking pre-flight socket probe (returns in ~50ms if offline)."""
    try:
        parsed = urlparse(url_str)
        host = parsed.hostname or "localhost"
        port = parsed.port or default_port
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


raw_db_url = os.getenv("DATABASE_URL")
default_sqlite_path = os.path.join(backend_root, "wanderwise.db")
default_sqlite_url = f"sqlite:///{default_sqlite_path.replace(os.sep, '/')}"

engine = None
active_db_url = None

if raw_db_url and raw_db_url.startswith("postgresql"):
    if _is_service_reachable(raw_db_url):
        try:
            test_engine = create_engine(
                raw_db_url,
                connect_args={"connect_timeout": 2},
                pool_pre_ping=True
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine = test_engine
            active_db_url = raw_db_url
            logger.info("[Database] Connected to PostgreSQL successfully.")
        except Exception as e:
            logger.warning(f"[Database] PostgreSQL error ({e}). Falling back to local SQLite at {default_sqlite_path}.")
            engine = create_engine(default_sqlite_url, connect_args={"check_same_thread": False})
            active_db_url = default_sqlite_url
    else:
        logger.info(
            f"[Database] PostgreSQL service not detected on target port. "
            f"Falling back to local SQLite database: {default_sqlite_path}"
        )
        engine = create_engine(default_sqlite_url, connect_args={"check_same_thread": False})
        active_db_url = default_sqlite_url
elif raw_db_url and raw_db_url.startswith("sqlite"):
    engine = create_engine(raw_db_url, connect_args={"check_same_thread": False})
    active_db_url = raw_db_url
else:
    logger.info(f"[Database] DATABASE_URL unset. Using local SQLite at: {default_sqlite_path}")
    engine = create_engine(default_sqlite_url, connect_args={"check_same_thread": False})
    active_db_url = default_sqlite_url

DATABASE_URL = active_db_url
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
