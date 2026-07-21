from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Dict, Any
import logging

from app.core.config import settings
from app.core.security import hash_password, normalize_email
from app.core.seed_mitsumi import seed_mitsumi

logger = logging.getLogger(__name__)
# MONGODB CONNECTION

class MongoDBManager:
    """Manages MongoDB connections and operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to MongoDB"""
        if self._connected:
            return
        
        try:
            # Use resolved URL from settings (fetches from AWS Secrets in production)
            mongo_url = settings.resolved_mongodb_url if hasattr(settings, 'resolved_mongodb_url') else settings.MONGODB_URL
            
            self.client = AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                retryReads=True,
            )
            self.db = self.client[settings.MONGODB_DB]
            
            # Test connection
            await self.client.admin.command('ping')
            self._connected = True
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB}")
            
        except Exception as e:
            logger.error(f" Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info(" MongoDB connection closed")
    
    def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if not self._connected or not self.db:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.db
    
    def get_client(self) -> AsyncIOMotorClient:
        """Get client instance"""
        if not self._connected or not self.client:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.client
    
    @property
    def is_connected(self) -> bool:
        return self._connected

# SINGLETON INSTANCE

mongo_manager = MongoDBManager()

# For backward compatibility
mongo_client = None
mongo_db = None

async def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client (initializes if needed)"""
    if not mongo_manager.is_connected:
        await mongo_manager.connect()
    return mongo_manager.get_client()

async def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database (initializes if needed)"""
    if not mongo_manager.is_connected:
        await mongo_manager.connect()
    return mongo_manager.get_db()

# MODULES & PERMISSIONS

# Full capability set exposed to the super_admin role
ALL_MODULES = [
    "dashboard",
    "tasks",
    "tool_results",
    "agent:sales",
    "agent:marketing",
    "agent:finance",
    "agent:ops",
    "department:sales",
    "department:marketing",
    "department:finance",
    "department:ops",
    "settings",
    "settings:regions",
    "settings:roles",
    "settings:users",
    "preferences",
    "user_management",
    "billing",
    "audit_logs",
]

# SEED DATABASE

async def seed_mongo() -> None:
    """Seed MongoDB with initial data and indexes"""
    try:
        db = await get_mongo_db()
        
        users = db["users"]
        chats = db["chats"]
        messages = db["messages"]
        auth_otps = db["auth_otps"]
        reset_tokens = db["reset_tokens"]
        sessions = db["sessions"]

        # CREATE INDEXES
        
        # Users
        await users.create_index("email", unique=True)
        await users.create_index("username", unique=True, sparse=True)
        await users.create_index([("created_at", -1)])
        
        # Chats
        await chats.create_index([
            ("user_id", 1),
            ("agent_name", 1),
            ("is_deleted", 1),
            ("pinned", -1),
            ("updated_at", -1)
        ])
        await chats.create_index([("user_id", 1), ("updated_at", -1)])
        await chats.create_index([("session_id", 1)])
        
        # Messages
        await messages.create_index([("chat_id", 1), ("created_at", 1)])
        await messages.create_index([("chat_id", 1), ("role", 1)])
        await messages.create_index([("session_id", 1)])
        
        # Auth OTPs
        await auth_otps.create_index("email")
        await auth_otps.create_index("purpose")
        await auth_otps.create_index("expires_at", expireAfterSeconds=0)
        await auth_otps.create_index([("email", 1), ("purpose", 1)])
        
        # Reset Tokens
        await reset_tokens.create_index("email")
        await reset_tokens.create_index("expires_at", expireAfterSeconds=0)
        
        # Sessions (for WebSocket)
        await sessions.create_index("session_id", unique=True)
        await sessions.create_index([("user_id", 1), ("last_activity", -1)])
        await sessions.create_index("expires_at", expireAfterSeconds=0)
        
        # SEED SUPERADMIN
        
        await _upsert_superadmin(users)
        
        # SEED DEMO DATA
        
        # Full Mitsumi demo catalogue: customers, principals, leads, quotes, orders,
        # inventory, pricing, invoices, campaigns, tickets, shipments, knowledge base.
        # Idempotent per-collection, safe to re-run on every boot.
        await seed_mitsumi(db)
        
        logger.info(" MongoDB seeded successfully!")
        
    except Exception as e:
        logger.error(f" Failed to seed MongoDB: {e}")
        raise

# SUPERADMIN HELPER

async def _upsert_superadmin(users) -> None:
    """Create or update superadmin user"""
    email = normalize_email(settings.SUPERADMIN_EMAIL)
    
    update = {
        "$set": {
            "email": email,
            "name": settings.SUPERADMIN_NAME,
            "roles": ["super_admin"],
            "modules": ALL_MODULES,
            "is_super_admin": True,
            "updated_at": "NOW",
        },
        "$setOnInsert": {
            "password_hash": hash_password(settings.SUPERADMIN_PASSWORD),
            "created_at": "NOW",
            "is_active": True,
            "email_verified": True,
        },
    }
    
    result = await users.update_one({"email": email}, update, upsert=True)
    
    if result.upserted_id:
        logger.info(f" Superadmin created: {email}")
    else:
        logger.info(f"Superadmin updated: {email}")

# USER HELPER FUNCTIONS

def user_has_module(user: dict, module: str) -> bool:
    """Check if user has access to a module"""
    if user.get("is_super_admin"):
        return True
    modules = user.get("modules") or []
    return module in modules

def user_has_role(user: dict, role: str) -> bool:
    """Check if user has a specific role"""
    if user.get("is_super_admin"):
        return True
    roles = user.get("roles") or []
    return role in roles

def user_can_access_agent(user: dict, agent_name: str) -> bool:
    """Check if user can access a specific agent"""
    if user.get("is_super_admin"):
        return True
    
    # Check if user has agent-specific permission
    agent_module = f"agent:{agent_name}"
    modules = user.get("modules") or []
    
    # Check specific agent permission
    if agent_module in modules:
        return True
    
    # Check wildcard agent permission
    if "agent:*" in modules:
        return True
    
    return False

# LIFECYCLE HELPERS

async def ensure_connection() -> None:
    """Ensure MongoDB connection exists"""
    if not mongo_manager.is_connected:
        await mongo_manager.connect()

async def close_connection() -> None:
    """Close MongoDB connection"""
    await mongo_manager.disconnect()

# COMPATIBILITY

# For backward compatibility with existing code
# Initialize on first use instead of at import
async def get_mongo_client_compat() -> AsyncIOMotorClient:
    """Backward compatibility: returns client"""
    return await get_mongo_client()

async def get_mongo_db_compat() -> AsyncIOMotorDatabase:
    """Backward compatibility: returns db"""
    return await get_mongo_db()