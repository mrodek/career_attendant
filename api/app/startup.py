"""
Database initialization and startup tasks
"""
import os
from .db import Base, engine
from .logger import logger
from . import models  # Import models to register them


def init_db(drop_all: bool = False):
    """
    Create all database tables if they don't exist.
    This is called on application startup.
    
    Args:
        drop_all: If True, drop all tables before creating (DANGEROUS - dev only!)
    """
    try:
        if drop_all:
            logger.warning("⚠️  DROP_ALL_TABLES is enabled - dropping all tables!")
            Base.metadata.drop_all(bind=engine)
            logger.info("All tables dropped")
        
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Log registered tables
        table_names = Base.metadata.tables.keys()
        logger.info(f"Registered tables: {', '.join(table_names)}")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
