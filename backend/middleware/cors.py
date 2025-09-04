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
        
        self.cors_rules = {
            "/api/auth/token": {
                "allow_origins": self.cors_origins,
                "allow_credentials": True,
                "allow_methods": ["POST"],
                "allow_headers": ["content-type", "authorization"]
            }
        }
    
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
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        cors_rule = None

        for rule_path, rule in self.cors_rules.items():
            if path == rule_path or (rule_path.endswith("/") and path.startswith(rule_path)):
                cors_rule = rule
                break
        
        # Handle OPTIONS preflight requests
        if request.method == "OPTIONS" and cors_rule:
            origin = request.headers.get("origin")
            if origin in cors_rule["allow_origins"]:
                response = JSONResponse(
                    content={"message": "OK"},
                    status_code=200
                )
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = str(cors_rule["allow_credentials"]).lower()
                response.headers["Access-Control-Allow-Methods"] = ", ".join(cors_rule["allow_methods"])
                response.headers["Access-Control-Allow-Headers"] = ", ".join(cors_rule["allow_headers"])
                response.headers["Access-Control-Max-Age"] = "86400"
                return response
            else:
                return JSONResponse(
                    status_code=403,
                    content={"detail": f"CORS policy violation for {path}"},
                    headers={"Access-Control-Allow-Origin": "null"}
                )
        
        # Check Origin for normal requests
        if cors_rule:
            origin = request.headers.get("origin")
            if origin and origin not in cors_rule["allow_origins"]:
                return JSONResponse(
                    status_code=403,
                    content={"detail": f"CORS policy violation for {path}"},
                    headers={"Access-Control-Allow-Origin": "null"}
                )
        
        response = await call_next(request)
        
        # Set CORS headers
        if cors_rule:
            origin = request.headers.get("origin")
            if origin in cors_rule["allow_origins"]:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = str(cors_rule["allow_credentials"]).lower()
                response.headers["Access-Control-Allow-Methods"] = ", ".join(cors_rule["allow_methods"])
                response.headers["Access-Control-Allow-Headers"] = ", ".join(cors_rule["allow_headers"])
        
        return response

def add_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom path specific CORS middleware
    app.add_middleware(PathSpecificCORSMiddleware)