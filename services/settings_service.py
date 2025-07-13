import logging
import os
import psutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)

class SettingsService:
    """Service class for system settings and configuration management."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.version = "1.0.0"
        self.recent_errors = []
    
    def get_system_settings(self) -> Dict[str, Any]:
        """Get current system settings for admin viewing."""
        try:
            return {
                "api_config": {
                    "host": settings.api_host,
                    "port": settings.api_port,
                    "debug": settings.debug
                },
                "database_config": {
                    "url": self._mask_sensitive_data(settings.database_url),
                    "chroma_db_path": settings.chroma_db_path
                },
                "ai_config": {
                    "model": settings.openai_model,
                    "api_key_configured": bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here"),
                    "temperature": settings.default_temperature,
                    "max_tokens": settings.max_tokens,
                    "embedding_model": settings.embedding_model
                },
                "rag_config": {
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap,
                    "max_retrieval_docs": settings.max_retrieval_docs
                },
                "chat_config": {
                    "max_conversation_history": settings.max_conversation_history,
                    "default_temperature": settings.default_temperature,
                    "max_tokens": settings.max_tokens
                },
                "security_config": {
                    "algorithm": settings.algorithm,
                    "access_token_expire_minutes": settings.access_token_expire_minutes,
                    "secret_key_configured": bool(settings.secret_key and settings.secret_key != "your_secret_key_here_change_in_production")
                }
            }
        except Exception as e:
            logger.error(f"Error getting system settings: {e}")
            return {}
    
    def update_settings(self, category: str, new_settings: Dict[str, Any]) -> bool:
        """Update system settings (limited to runtime settings)."""
        try:
            if category == "ai":
                # Update AI-related settings
                if "temperature" in new_settings:
                    settings.default_temperature = float(new_settings["temperature"])
                if "max_tokens" in new_settings:
                    settings.max_tokens = int(new_settings["max_tokens"])
                
            elif category == "rag":
                # Update RAG-related settings
                if "chunk_size" in new_settings:
                    settings.chunk_size = int(new_settings["chunk_size"])
                if "chunk_overlap" in new_settings:
                    settings.chunk_overlap = int(new_settings["chunk_overlap"])
                if "max_retrieval_docs" in new_settings:
                    settings.max_retrieval_docs = int(new_settings["max_retrieval_docs"])
                
            elif category == "chat":
                # Update chat-related settings
                if "max_conversation_history" in new_settings:
                    settings.max_conversation_history = int(new_settings["max_conversation_history"])
                if "temperature" in new_settings:
                    settings.default_temperature = float(new_settings["temperature"])
                if "max_tokens" in new_settings:
                    settings.max_tokens = int(new_settings["max_tokens"])
                
            elif category == "security":
                # Update security-related settings
                if "access_token_expire_minutes" in new_settings:
                    settings.access_token_expire_minutes = int(new_settings["access_token_expire_minutes"])
                
            else:
                logger.warning(f"Unknown settings category: {category}")
                return False
            
            logger.info(f"Updated {category} settings successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating {category} settings: {e}")
            return False
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview for admin dashboard."""
        try:
            return {
                "system_health": self._get_system_health(),
                "resource_usage": self._get_resource_usage(),
                "recent_errors": self._get_recent_errors(),
                "uptime": self._get_uptime(),
                "version_info": self._get_version_info()
            }
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {}
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            # Check database connection
            from database import get_db_context
            db_status = "healthy"
            try:
                with get_db_context() as db:
                    db.execute("SELECT 1")
            except Exception:
                db_status = "unhealthy"
            
            # Check vector store
            vector_status = "healthy"
            try:
                from services.rag_service import rag_service
                # Simple check - if we can access the collection
                rag_service.get_collection_stats()
            except Exception:
                vector_status = "unhealthy"
            
            # Check OpenAI connection
            openai_status = "healthy" if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here" else "not_configured"
            
            overall_status = "healthy"
            if db_status == "unhealthy" or vector_status == "unhealthy":
                overall_status = "degraded"
            if openai_status == "not_configured":
                overall_status = "degraded"
            
            return {
                "overall": overall_status,
                "database": db_status,
                "vector_store": vector_status,
                "openai": openai_status,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                "overall": "unknown",
                "database": "unknown",
                "vector_store": "unknown",
                "openai": "unknown",
                "last_check": datetime.utcnow().isoformat()
            }
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_mb": round(memory.total / (1024 * 1024), 2),
                    "available_mb": round(memory.available / (1024 * 1024), 2),
                    "used_mb": round(memory.used / (1024 * 1024), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                    "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                    "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                    "percent": round((disk.used / disk.total) * 100, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {
                "cpu_percent": 0,
                "memory": {"total_mb": 0, "available_mb": 0, "used_mb": 0, "percent": 0},
                "disk": {"total_gb": 0, "free_gb": 0, "used_gb": 0, "percent": 0}
            }
    
    def _get_recent_errors(self) -> list:
        """Get recent system errors."""
        # In a real implementation, this would read from a logging system
        # For now, return placeholder data
        return [
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "level": "ERROR",
                "message": "Failed to process document upload",
                "component": "RAG Service"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "level": "WARNING",
                "message": "High memory usage detected",
                "component": "System Monitor"
            }
        ]
    
    def _get_uptime(self) -> str:
        """Get system uptime."""
        try:
            uptime_duration = datetime.utcnow() - self.start_time
            days = uptime_duration.days
            hours, remainder = divmod(uptime_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days} days, {hours} hours, {minutes} minutes"
            elif hours > 0:
                return f"{hours} hours, {minutes} minutes"
            else:
                return f"{minutes} minutes, {seconds} seconds"
                
        except Exception as e:
            logger.error(f"Error calculating uptime: {e}")
            return "Unknown"
    
    def _get_version_info(self) -> Dict[str, Any]:
        """Get version information."""
        try:
            import sys
            return {
                "app_version": self.version,
                "python_version": sys.version,
                "platform": sys.platform,
                "build_date": "2024-01-01"  # This would be set during build
            }
        except Exception as e:
            logger.error(f"Error getting version info: {e}")
            return {}
    
    def _mask_sensitive_data(self, data: str) -> str:
        """Mask sensitive data in configuration."""
        if not data:
            return ""
        
        # Simple masking - show first 3 and last 3 characters
        if len(data) > 6:
            return data[:3] + "*" * (len(data) - 6) + data[-3:]
        else:
            return "*" * len(data)
    
    def log_error(self, error: str, component: str = "Unknown"):
        """Log an error for admin monitoring."""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": error,
            "component": component
        }
        self.recent_errors.append(error_entry)
        
        # Keep only last 100 errors
        if len(self.recent_errors) > 100:
            self.recent_errors = self.recent_errors[-100:]

# Global settings service instance
settings_service = SettingsService() 