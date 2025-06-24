from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Address


def get_real_ip(request: Request) -> str:
    """
    Get the real client IP address, prioritizing proxy headers
    
    Priority order:
    1. X-Forwarded-For (takes first IP, usually the original client)
    2. X-Real-IP (real IP set by nginx)
    3. request.client.host (direct connection IP)
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Real client IP address
    """
    # First try X-Forwarded-For
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Then try X-Real-IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"


class RealIPMiddleware(BaseHTTPMiddleware):    
    async def dispatch(self, request: Request, call_next):
        real_ip = get_real_ip(request)
        if request.client and real_ip != "unknown" and real_ip != request.client.host:
            # Keep original port but use real IP
            original_port = request.client.port
            request.scope["client"] = Address(real_ip, original_port)
        
        response = await call_next(request)
        return response


def add_real_ip_middleware(app):
    app.add_middleware(RealIPMiddleware) 