import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BaseServiceException(Exception):
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = None,
        log_level: str = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if log_level is not None:
            self.log_level = log_level
        
        log_msg = f"[{self.error_code}] | {self.message}"

        if self.log_level == "error":
            logger.error(log_msg)
        elif self.log_level == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        super().__init__(self.message)

class ServerException(BaseServiceException):
    """Server exception"""
    def __init__(self, message: str = "Server error", status_code: int = 500, details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="SERVER_ERROR", details=details, status_code=status_code, log_level="error")