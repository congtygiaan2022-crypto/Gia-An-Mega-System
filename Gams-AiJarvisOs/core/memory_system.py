import time
import logging
from database.mysql_connector import mysql_connector, AgentMemory
from database.redis_connector import redis_connector

logger = logging.getLogger("MemorySystem")

class MemorySystem:
    """
    Jarvis OS Agent Memory System
    - Short Term Memory: Redis (fast, ephemeral)
    - Long Term Memory: MySQL (slow, persistent)
    """
    def __init__(self):
        self.mysql = mysql_connector
        self.redis = redis_connector
        # Initialize MySQL tables
        self.mysql.init_db()

    def store_short_term(self, agent_name, key, content, ex=3600):
        """Stores ephemeral memory in Redis."""
        redis_key = f"mem:{agent_name}:{key}"
        return self.redis.set_cache(redis_key, content, ex=ex)

    def get_short_term(self, agent_name, key):
        """Retrieves ephemeral memory from Redis."""
        redis_key = f"mem:{agent_name}:{key}"
        return self.redis.get_cache(redis_key)

    def store_long_term(self, agent_name, category, content):
        """Stores persistent memory in MySQL."""
        session = self.mysql.get_session()
        try:
            entry = AgentMemory(
                agent_name=agent_name,
                category=category,
                content=content,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S') # Or datetime object
            )
            # Adjust timestamp to datetime object if needed for SQLAlchemy
            from datetime import datetime
            entry.timestamp = datetime.utcnow()
            
            session.add(entry)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing long term memory: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_long_term(self, agent_name, category=None, limit=50):
        """Retrieves persistent memory from MySQL."""
        session = self.mysql.get_session()
        try:
            query = session.query(AgentMemory).filter(AgentMemory.agent_name == agent_name)
            if category:
                query = query.filter(AgentMemory.category == category)
            
            results = query.order_by(AgentMemory.timestamp.desc()).limit(limit).all()
            return [{"category": r.category, "content": r.content, "timestamp": str(r.timestamp)} for r in results]
        except Exception as e:
            logger.error(f"Error getting long term memory: {e}")
            return []
        finally:
            session.close()

# Global instance
memory_system = MemorySystem()

# Global instance
memory_system = MemorySystem()
