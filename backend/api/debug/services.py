from fastapi import Request
from utils import get_real_ip
from .schema import IPDebugResponse

async def get_ip_debug_info(request: Request) -> IPDebugResponse:
    return {
        "client_host": request.client.host if request.client else None,
        "x_forwarded_for": request.headers.get("x-forwarded-for"),
        "x_real_ip": request.headers.get("x-real-ip"),
        "detected_real_ip": get_real_ip(request),
        "middleware_processed": True,
        "note": "If middleware works correctly, client_host should equal detected_real_ip"
    }