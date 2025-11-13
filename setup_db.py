#!/usr/bin/env python3
"""
Database setup script.
Creates tables and initializes the database.
"""

import sys
from loguru import logger

from src.utils.database import init_db, engine
from src.utils.models import Base

def setup_database():
    """Initialize the database."""
    logger.info("Setting up database...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")

        logger.info("Database setup complete!")
        return True

    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
