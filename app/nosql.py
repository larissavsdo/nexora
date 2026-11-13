from pymongo import MongoClient, ASCENDING, DESCENDING
from redis import Redis
from app.config import settings

mongo_client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
mongo_db = mongo_client[settings.mongodb_database]
messages = mongo_db["messages"]
messages.create_index([("ticket_id", ASCENDING), ("created_at", DESCENDING)])
messages.create_index([("content", "text")])
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
