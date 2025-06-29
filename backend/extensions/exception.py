from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail if exc.detail else "HTTP Error"
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = {}
        for err in exc.errors():
            field = ".".join([str(loc) for loc in err["loc"] if isinstance(loc, (str, int))])
            errors[field] = err["msg"]
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "Validation Error",
                "data": errors
            }
        )

    @app.exception_handler(Exception)
    async def internal_server_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal Server Error",
                "data": None
            }
        )