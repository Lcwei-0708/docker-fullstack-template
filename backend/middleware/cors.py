from core.config import settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class PathSpecificCORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
        self.allowed_hosts = [
            f"{settings.HOSTNAME}:{settings.BACKEND_PORT}",
            f"localhost:{settings.BACKEND_PORT}",
            f"{settings.HOSTNAME}:{settings.FRONTEND_PORT}",
            f"localhost:{settings.FRONTEND_PORT}"
        ]
        
        self.generate_cors_origins()
        
        self.whitelist_paths = [
            # Add whitelist paths here (e.g. "/api/example/")
        ]
    
    def generate_cors_origins(self):
        """Generate HTTP and HTTPS versions of the sources"""
        self.cors_origins = []
        for host in self.allowed_hosts:
            if host == "*":
                self.cors_origins.append("*")
                continue
            self.cors_origins.extend([
                f"http://{host}",
                f"https://{host}"
            ])
    
    def is_whitelist_path(self, path: str) -> bool:
        """Check if path is in whitelist"""
        for whitelist_path in self.whitelist_paths:
            if path == whitelist_path or (whitelist_path.endswith("/") and path.startswith(whitelist_path)):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS requests"""
        path = request.url.path
        
        if self.is_whitelist_path(path):
            response = await call_next(request)
            return response
        
        origin = request.headers.get("origin")
        if origin and origin not in self.cors_origins:
            return JSONResponse(
                status_code=403,
                content={"detail": f"CORS policy violation for {path}"},
                headers={"Access-Control-Allow-Origin": "null"}
            )
        
        response = await call_next(request)
        if origin in self.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

def add_cors_middleware(app: FastAPI):
    app.add_middleware(PathSpecificCORSMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )