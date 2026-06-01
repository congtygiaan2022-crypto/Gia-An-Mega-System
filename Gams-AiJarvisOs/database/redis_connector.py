import os
import redis
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("RedisConnector")

class RedisConnector:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    def ping(self):
        if not self.client: return False
        try:
            return self.client.ping()
        except:
            return False

    # --- Queue Operations ---
    def push_task(self, queue_name, task_data):
        """Pushes a task to a designated queue."""
        if not self.client: return False
        try:
            self.client.rpush(queue_name, json.dumps(task_data))
            return True
        except Exception as e:
            logger.error(f"Redis push error: {e}")
            return False

    def pop_task(self, queue_name, timeout=0):
        """Pops a task from a designated queue (blocking)."""
        if not self.client: return None
        try:
            result = self.client.blpop(queue_name, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        except Exception as e:
            logger.error(f"Redis pop error: {e}")
            return None

    # --- Pub/Sub for Real-time Messaging ---
    def publish_message(self, channel, message):
        if not self.client: return False
        try:
            self.client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Redis publish error: {e}")
            return False

    # --- Cache / Short-term Memory ---
    def set_cache(self, key, value, ex=None):
        if not self.client: return False
        try:
            self.client.set(key, json.dumps(value), ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def get_cache(self, key):
        if not self.client: return None
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

# Global instance
redis_connector = RedisConnector()

if __name__ == "__main__":
    if redis_connector.ping():
        print("Redis connection successful!")
    else:
        print("Redis connection failed.")
