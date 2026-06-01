import os
import logging
from sqlalchemy import create_all, create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MySQLConnector")

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    plugin = Column(String(100))
    schedule = Column(String(100))
    accounts = Column(JSON)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    steps = Column(JSON) # List of steps
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentMemory(Base):
    __tablename__ = 'agent_memory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False) # e.g., 'task_history', 'insight'
    content = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class MySQLConnector:
    def __init__(self):
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.database = os.getenv("MYSQL_DATABASE", "jarvis_os")
        
        # Use mysql-connector-python as driver
        self.engine = create_engine(f'mysql+mysqlconnector://{self.user}:{self.password}@{self.host}/{self.database}')
        self.Session = sessionmaker(bind=self.engine)

    def init_db(self):
        """Creates tables if they don't exist."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("MySQL Tables initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MySQL: {e}")
            return False

    def get_session(self):
        return self.Session()

# Global instance
mysql_connector = MySQLConnector()

if __name__ == "__main__":
    # Test connection and init
    mysql_connector.init_db()
