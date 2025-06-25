import logging
from utils import parse_responses
from .schema import IPDebugResponse
from fastapi import APIRouter, Request
from .services import get_ip_debug_info

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debug"])

@router.get("/test-ip", 
            response_model=IPDebugResponse,
            summary="Test IP detection",
            responses=parse_responses({
                200: ("IP detection successful", IPDebugResponse),
                400: ("Invalid IP address", None),
                500: ("Internal Server Error", None),
            })
)
async def test_ip_detection(request: Request):
    return await get_ip_debug_info(request)