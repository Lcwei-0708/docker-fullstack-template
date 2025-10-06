import logging
from fastapi_limiter.depends import RateLimiter
from utils.response import parse_responses, APIResponse
from .services import get_ip_debug_info, clear_blocked_ips
from .schema import IPDebugResponse, ClearBlockedIPsResponse
from fastapi import APIRouter, Request, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Debug"])

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
    try:
        response = await get_ip_debug_info(request)
        return APIResponse(code=200, message="IP detection successful", data=response)
    except Exception:
        raise HTTPException(status_code=500)

@router.delete(
    "/clear-blocked-ip",
    summary="Clear all blocked IPs in Redis",
    response_model=APIResponse[ClearBlockedIPsResponse],
    responses=parse_responses({
        200: ("Blocked IPs cleared successfully", ClearBlockedIPsResponse),
        500: ("Internal Server Error", None),
    })
)
async def clear_blocked_ips_api():
    try:
        result = await clear_blocked_ips()
        return APIResponse(
            code=200,
            message="Blocked IPs cleared successfully",
            data=result
        )
    except Exception:
        raise HTTPException(status_code=500)