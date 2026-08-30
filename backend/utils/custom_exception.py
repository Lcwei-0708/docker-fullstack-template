import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("exception")

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
        self.log_level = log_level
        if status_code is not None:
            self.status_code = status_code

        if self.log_level == "error":
            logger.error(self.message)
        elif self.log_level == "warning":
            logger.warning(self.message)
        elif self.log_level == "info":
            logger.info(self.message)

        super().__init__(self.message)

class ServerException(BaseServiceException):
    """Server exception"""
    def __init__(self, message: str = "Server error", status_code: int = 500, details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="SERVER_ERROR", details=details, status_code=status_code, log_level="error")

class AuthenticationException(BaseServiceException):
    """Authentication related exceptions"""
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="AUTH_ERROR", details=details, status_code=401)

class PasswordResetRequiredException(BaseServiceException):
    """Password reset required exception"""
    def __init__(self, message: str = "Password reset required", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="PASSWORD_RESET_REQUIRED", details=details, status_code=202)

class EmailVerificationRequiredException(BaseServiceException):
    """Email verification required exception"""
    def __init__(self, message: str = "Email verification required", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="EMAIL_VERIFICATION_REQUIRED", details=details, status_code=202)

class AuthorizationException(BaseServiceException):
    """Authorization related exceptions"""
    def __init__(self, message: str = "Permission denied", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="PERMISSION_ERROR", details=details, status_code=403)

class ValidationException(BaseServiceException):
    """Validation related exceptions"""
    def __init__(self, message: str = "Validation failed", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="VALIDATION_ERROR", details=details, status_code=400)

class NotFoundException(BaseServiceException):
    """Resource not found exceptions"""
    def __init__(self, message: str = "Resource not found", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="NOT_FOUND", details=details, status_code=404)

class ConflictException(BaseServiceException):
    """Resource conflict exceptions"""
    def __init__(self, message: str = "Resource conflict", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="CONFLICT", details=details, status_code=409)

class TokenException(BaseServiceException):
    """Token related exceptions"""
    def __init__(self, message: str = "Token error", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="TOKEN_ERROR", details=details, status_code=401)

class SMTPNotConfiguredException(BaseServiceException):
    """SMTP configuration related exceptions"""
    def __init__(self, message: str = "SMTP is not configured", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="SMTP_NOT_CONFIGURED", details=details, status_code=503)

class RegistrationDisabledException(BaseServiceException):
    """Registration disabled exception"""
    def __init__(self, message: str = "Registration is disabled", details: Dict[str, Any] = None):
        super().__init__(message=message, error_code="REGISTRATION_DISABLED", details=details, status_code=503)
