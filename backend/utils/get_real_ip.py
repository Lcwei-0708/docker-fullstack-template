from fastapi import Request

def get_real_ip(request: Request) -> str:
    """
    Get the real client IP address from the trusted reverse proxy.

    Priority order:
    1. X-Real-IP (set by nginx from $remote_addr — not client-controlled)
    2. request.client.host (direct connection IP)

    Do not trust X-Forwarded-For here: with nginx $proxy_add_x_forwarded_for,
    a client-supplied value is prepended and would spoof rate-limit keys.
    """
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"
