"""
Database configuration and initialization module.

This module sets up SQLAlchemy with PostgreSQL, handling database connections
and session management.

Environment Variables Required:
    DB_USER: Database username
    DB_PASSWORD: Database password
    DB_HOST: Database host (defaults to 'localhost')
    DB_PORT: Database port (defaults to '5432')
    DB_NAME: Database name
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

# Construct database URL from environment variables
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Base class for declarative models
Base = declarative_base()

# Session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables if they don't exist."""
    from models.documents import Documents
    from models.embeddings import Embeddings
    from models.user import User
    from models.api_list import APIList
    from models.chat_sessions import ChatSession
    
    # Get all tables that should exist
    tables = [User, APIList, Documents, Embeddings, ChatSession]
    
    try:
        # Get inspector to check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Create tables that don't exist
        for table in tables:
            if table.__tablename__ not in existing_tables:
                table.__table__.create(bind=engine)
                print(f"Created table: {table.__tablename__}")
    except SQLAlchemyError as e:
        print("Error during database initialization:", e)


def get_db():
    """
    Dependency to get database session.
    
    Yields:
        Session: Database session that will be automatically closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
