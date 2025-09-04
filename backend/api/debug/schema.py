from typing import Optional, List
from pydantic import BaseModel, Field

class IPDebugResponse(BaseModel):
    client_host: Optional[str] = Field(..., description="Client host")
    x_forwarded_for: Optional[str] = Field(..., description="X-Forwarded-For")
    x_real_ip: Optional[str] = Field(..., description="X-Real-IP")
    detected_real_ip: Optional[str] = Field(..., description="Detected real IP")

class ClearBlockedIPsResponse(BaseModel):
    cleared_ips: List[str] = Field(..., description="Cleared blocked IPs")
    count: int = Field(..., description="Number of cleared IPs")