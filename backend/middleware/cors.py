from core.config import settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse

class CORSMiddleware(BaseHTTPMiddleware):
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
    
    def _normalize_origin(self, origin: str) -> str:
        """Normalize origin for comparison"""
        try:
            parsed = urlparse(origin)
            port = parsed.port
            if port is None:
                port = 443 if parsed.scheme == "https" else 80
            return f"{parsed.scheme}://{parsed.hostname}:{port}"
        except Exception:
            return origin.lower()
    
    def is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed, with normalized comparison"""
        if not origin:
            return False
        
        normalized_origin = self._normalize_origin(origin)
        
        for allowed in self.cors_origins:
            if allowed == "*":
                continue
            
            try:
                normalized_allowed = self._normalize_origin(allowed)
                if normalized_origin == normalized_allowed:
                    return True
            except Exception:
                pass
        
        return origin.lower() in [a.lower() for a in self.cors_origins if a != "*"]
    
    def get_allowed_headers(self, request: Request) -> str:
        """Get allowed headers string for CORS response"""
        allowed_headers = [
            "content-type",
            "authorization",
            "accept",
            "accept-language",
            "cache-control",
            "pragma",
            "x-requested-with",
        ]
        
        requested_headers = request.headers.get("access-control-request-headers", "")
        if requested_headers:
            requested_list = [h.strip().lower() for h in requested_headers.split(",")]
            allowed_headers.extend(requested_list)
        
        allowed_headers = sorted(list(set(allowed_headers)))
        return ", ".join(allowed_headers)
    
    def _should_allow_origin(self, origin: str, is_whitelisted: bool) -> bool:
        """Check if origin should be allowed"""
        if is_whitelisted:
            return bool(origin)
        return origin and self.is_allowed_origin(origin)
    
    def _set_cors_origin_headers(self, headers: dict, origin: str):
        """Set CORS origin and credentials headers"""
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
    
    def handle_preflight(self, request: Request, origin: str, is_whitelisted: bool) -> JSONResponse:
        """Handle OPTIONS preflight requests"""
        if not self._should_allow_origin(origin, is_whitelisted):
            return JSONResponse(status_code=200, content={})
        
        allowed_headers_str = self.get_allowed_headers(request)
        
        headers = {
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": allowed_headers_str,
            "Access-Control-Max-Age": "3600",
            "Vary": "Origin",
        }
        
        self._set_cors_origin_headers(headers, origin)
        return JSONResponse(status_code=200, content={}, headers=headers)
    
    def add_cors_headers(self, response, origin: str, is_whitelisted: bool):
        """Add CORS headers to response"""
        response.headers["Vary"] = "Origin"
        
        if not self._should_allow_origin(origin, is_whitelisted):
            return
        
        self._set_cors_origin_headers(response.headers, origin)
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "content-type, authorization, accept, accept-language, cache-control, pragma, x-requested-with"
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS requests"""
        path = request.url.path
        origin = request.headers.get("origin")
        is_whitelisted = self.is_whitelist_path(path)
        
        if request.method == "OPTIONS":
            return self.handle_preflight(request, origin, is_whitelisted)
        
        response = await call_next(request)
        self.add_cors_headers(response, origin, is_whitelisted)
        return response

def add_cors_middleware(app: FastAPI):
    app.add_middleware(CORSMiddleware)