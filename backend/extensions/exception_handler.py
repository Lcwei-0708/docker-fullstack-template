from utils.response import APIResponse
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        status_code = exc.status_code
        
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            return JSONResponse(
                status_code=status_code,
                content=exc.detail
            )
        
        message = exc.detail if exc.detail else "HTTP Error"
        data = None
        
        resp = APIResponse(code=status_code, message=message, data=data)
        return JSONResponse(
            status_code=status_code,
            content=resp.dict(exclude_none=True)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = {}
        for err in exc.errors():
            field = ".".join([str(loc) for loc in err["loc"] if isinstance(loc, (str, int))])
            errors[field] = err["msg"]
        resp = APIResponse(code=422, message="Validation Error", data=errors)
        return JSONResponse(
            status_code=422,
            content=resp.dict(exclude_none=True)
        )

    @app.exception_handler(Exception)
    async def internal_server_error_handler(request: Request, exc: Exception):
        resp = APIResponse(code=500, message="Internal Server Error", data=None)
        return JSONResponse(
            status_code=500,
            content=resp.dict(exclude_none=True)
        )