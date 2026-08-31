from pydantic import BaseModel, Field


class IPDebugResponse(BaseModel):
    client_host: str | None = Field(..., description="Client host")
    x_forwarded_for: str | None = Field(..., description="X-Forwarded-For")
    x_real_ip: str | None = Field(..., description="X-Real-IP")
    detected_real_ip: str | None = Field(..., description="Detected real IP")


class ClearBlockedIPsResponse(BaseModel):
    cleared_ips: list[str] = Field(..., description="Cleared blocked IPs")
    count: int = Field(..., description="Number of cleared IPs")
