from fastapi import Request


def get_real_ip(request: Request) -> str:
    """
    Get the client IP address from the X-Real-IP header set by nginx.

    Nginx sets X-Real-IP from $remote_addr (TCP connection IP).

    Priority order:
    1. X-Real-IP (from nginx $remote_addr)
    2. request.client.host (fallback)
    """
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"
