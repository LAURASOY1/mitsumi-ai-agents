from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoManager:
    """Manage MongoDB collections and indexes"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(settings.resolved_mongodb_url)
        self.db = self.client[settings.MONGODB_DB]
        await self.ensure_indexes()
    
    async def ensure_indexes(self):
        """Create indexes on startup (like migrations)"""
        
        # Agent collection indexes
        await self.db.agents.create_index("name", unique=True)
        await self.db.agents.create_index("user_id")
        await self.db.agents.create_index([("created_at", -1)])
        
        # Sessions collection indexes
        await self.db.sessions.create_index("session_id", unique=True)
        await self.db.sessions.create_index([("last_activity", -1)])
        await self.db.sessions.create_index("user_id")
        
        # Messages collection indexes
        await self.db.messages.create_index([("session_id", 1), ("timestamp", -1)])
        await self.db.messages.create_index("agent_id")
        
        # Users collection indexes
        await self.db.users.create_index("email", unique=True)
        await self.db.users.create_index("username", unique=True)
        
        print("✅ MongoDB indexes created successfully!")
    
    async def migrate(self):
        """Run data migrations (if needed)"""
        
        # Example: Add new field to all documents
        result = await self.db.agents.update_many(
            {"version": {"$exists": False}},
            {"$set": {"version": "1.0.0"}}
        )
        print(f"✅ Updated {result.modified_count} agents with version field")
        
        # Example: Convert string to array
        result = await self.db.sessions.update_many(
            {"tags": {"$type": "string"}},
            [{"$set": {"tags": ["$tags"]}}]
        )
        print(f"✅ Updated {result.modified_count} sessions with tags array")
    
    async def get_collection(self, name):
        """Get a collection"""
        return self.db[name]

# Singleton instance
mongo_manager = MongoManager()
