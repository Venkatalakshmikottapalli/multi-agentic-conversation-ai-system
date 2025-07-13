from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from config import settings
from models.crm_models import Base
import logging

logger = logging.getLogger(__name__)

# Create the database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

class DatabaseManager:
    """Database manager for handling database operations."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all database tables."""
        create_tables()
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all database tables (for testing)."""
        Base.metadata.drop_all(bind=self.engine)
    
    def reset_database(self):
        """Reset the entire database (for testing)."""
        self.drop_tables()
        self.create_tables()

# Global database manager instance
db_manager = DatabaseManager()

# Initialize database on import
try:
    create_tables()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise 