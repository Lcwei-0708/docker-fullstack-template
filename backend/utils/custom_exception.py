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

class AuthenticationException(BaseServiceException):
    """Authentication related exceptions"""
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="AUTH_ERROR", details=details, status_code=401, log_level="warning")

class PasswordResetRequiredException(BaseServiceException):
    """Password reset required exception"""
    def __init__(self, message: str = "Password reset required", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="PASSWORD_RESET_REQUIRED", details=details, status_code=202, log_level="warning")

class AuthorizationException(BaseServiceException):
    """Authorization related exceptions"""
    def __init__(self, message: str = "Permission denied", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="PERMISSION_ERROR", details=details, status_code=403, log_level="warning")

class ValidationException(BaseServiceException):
    """Validation related exceptions"""
    def __init__(self, message: str = "Validation failed", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="VALIDATION_ERROR", details=details, status_code=400, log_level="warning")

class NotFoundException(BaseServiceException):
    """Resource not found exceptions"""
    def __init__(self, message: str = "Resource not found", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="NOT_FOUND", details=details, status_code=404, log_level="warning")

class ConflictException(BaseServiceException):
    """Resource conflict exceptions"""
    def __init__(self, message: str = "Resource conflict", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="CONFLICT", details=details, status_code=409, log_level="warning")

class TokenException(BaseServiceException):
    """Token related exceptions"""
    def __init__(self, message: str = "Token error", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="TOKEN_ERROR", details=details, status_code=401, log_level="warning")