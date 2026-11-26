from typing import Generator
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

# Ensure MySQLdb compatibility with PyMySQL
pymysql.install_as_MySQLdb()

settings = get_settings()


def _create_db_engine(url: str):
    if url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    kwargs = {"pool_pre_ping": True}
    if url.startswith("mysql"):
        kwargs["pool_recycle"] = 3600
        # PyMySQL does not accept 'ssl-mode' as a raw URL parameter.
        # Parse it out and pass it properly via connect_args={'ssl': ...}
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
        parsed = urlparse(url)
        if parsed.query:
            query_params = parse_qs(parsed.query)
            ssl_mode = (
                query_params.pop("ssl-mode", None)
                or query_params.pop("sslmode", None)
                or query_params.pop("ssl_mode", None)
            )
            if ssl_mode:
                new_query = urlencode([(k, v[0]) for k, v in query_params.items()])
                url = urlunparse(parsed._replace(query=new_query))
                mode_str = ssl_mode[0].upper() if isinstance(ssl_mode, list) else str(ssl_mode).upper()
                if mode_str in ("DISABLED", "DISABLE"):
                    kwargs["connect_args"] = {"ssl_disabled": True}
                else:
                    kwargs["connect_args"] = {"ssl": {"ssl_mode": mode_str}}
    elif url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _create_db_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Yield a database session per request and ensure cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
