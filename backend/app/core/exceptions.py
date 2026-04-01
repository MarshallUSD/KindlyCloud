"""Custom exceptions for the application."""
from typing import Any, Optional


class ApplicationException(Exception):
    """Base exception for the application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationException(ApplicationException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class AuthorizationException(ApplicationException):
    """Raised when user lacks permission."""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class NotFoundException(ApplicationException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class ConflictException(ApplicationException):
    """Raised when a resource already exists."""
    
    def __init__(self, message: str = "Resource already exists", **kwargs):
        super().__init__(message, status_code=409, **kwargs)


class ValidationException(ApplicationException):
    """Raised when validation fails."""
    
    def __init__(self, message: str = "Validation failed", **kwargs):
        super().__init__(message, status_code=400, **kwargs)
