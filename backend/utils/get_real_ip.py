from fastapi import Request

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