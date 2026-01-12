from database import get_database
from models import AuditLog
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class AuditService:
    async def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict = None,
        ip_address: str = None
    ):
        """Create audit log entry"""
        try:
            db = await get_database()
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                timestamp=datetime.now(timezone.utc),
                ip_address=ip_address
            )
            
            await db.audit_logs.insert_one(audit_log.model_dump())
            logger.info(f"Audit log created: {action} on {resource_type}:{resource_id} by {user_id}")
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")

audit_service = AuditService()
