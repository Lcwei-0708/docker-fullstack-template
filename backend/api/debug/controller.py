import logging
from fastapi import APIRouter, Request
from .services import get_ip_debug_info
from .schema import IPDebugResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debug"])

@router.get("/test-ip", response_model=IPDebugResponse)
async def test_ip_detection(request: Request):
    return await get_ip_debug_info(request)