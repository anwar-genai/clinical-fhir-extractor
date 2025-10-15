"""Audit logging utilities for security events"""

import logging
import json
from typing import Optional
from datetime import datetime

from fastapi import Request
from sqlalchemy.orm import Session

from .models import AuditLog

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    action: str,
    status: str,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[dict] = None
):
    """Log an audit event to the database"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details) if details else None
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(
            f"Audit: {action} by user_id={user_id} - {status}",
            extra={
                "action": action,
                "user_id": user_id,
                "status": status,
                "ip": ip_address
            }
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        db.rollback()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")

