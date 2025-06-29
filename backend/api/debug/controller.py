import logging
from .schema import IPDebugResponse
from .services import get_ip_debug_info
from utils import parse_responses, APIResponse
from fastapi import APIRouter, Request, Depends
from fastapi_limiter.depends import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debug"])

@router.get("/test-ip", 
            response_model=APIResponse[IPDebugResponse],
            summary="Test IP detection",
            responses=parse_responses({
                200: ("IP detection successful", IPDebugResponse),
                400: ("Invalid IP address", None),
                429: ("Too Many Requests", None),
                500: ("Internal Server Error", None),
            }),
            dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def test_ip_detection(request: Request):
    response = await get_ip_debug_info(request)
    return APIResponse(code=200, message="IP detection successful", data=response)