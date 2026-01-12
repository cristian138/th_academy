from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_db():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.mongo_url)
        db.db = db.client[settings.db_name]
        # Verify connection
        await db.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_db():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")

async def get_database():
    """Get database instance"""
    return db.db

async def create_indexes():
    """Create database indexes"""
    try:
        # Users indexes
        await db.db.users.create_index("email", unique=True)
        await db.db.users.create_index("role")
        
        # Contracts indexes
        await db.db.contracts.create_index("collaborator_id")
        await db.db.contracts.create_index("status")
        await db.db.contracts.create_index("created_by")
        
        # Documents indexes
        await db.db.documents.create_index("user_id")
        await db.db.documents.create_index("document_type")
        await db.db.documents.create_index("expiry_date")
        
        # Payments indexes
        await db.db.payments.create_index("contract_id")
        await db.db.payments.create_index("status")
        
        # Audit logs indexes
        await db.db.audit_logs.create_index("user_id")
        await db.db.audit_logs.create_index("timestamp")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
