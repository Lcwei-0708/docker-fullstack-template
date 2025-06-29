from fastapi import Request
from utils import get_real_ip
from starlette.datastructures import Address
from starlette.middleware.base import BaseHTTPMiddleware

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