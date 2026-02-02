"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from app.core.config import settings
from app.models.database import Base
from app.core.logging import app_logger


# Global engine and session factory (initialized later)
engine = None
SessionLocal = None


def initialize_database():
    """Initialize database engine and session factory"""
    global engine, SessionLocal
    
    # Check if database_url is configured
    if not settings.database_url:
        app_logger.error("Database URL not configured. Please provide a config file.")
        raise ValueError("Database URL not configured")
    
    # Create engine
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(
            settings.database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30.0,  # 30 second timeout for concurrent writes
            },
            poolclass=StaticPool,
        )
        
        # Enable WAL mode for better concurrent write performance
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")  # 30s busy timeout
            cursor.close()
    else:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    app_logger.info(f"Database initialized: {settings.database_url}")


def init_db():
    """Initialize database tables"""
    try:
        if engine is None:
            initialize_database()
        
        Base.metadata.create_all(bind=engine)
        app_logger.info("Database tables created successfully")
    except Exception as e:
        app_logger.error(f"Error creating database tables: {e}")
        raise


def get_db() -> Session:
    """Dependency for getting database session"""
    if SessionLocal is None:
        initialize_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session"""
    if SessionLocal is None:
        initialize_database()
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
