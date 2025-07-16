from typing import Optional
from pydantic import BaseModel

class IPDebugResponse(BaseModel):
    client_host: Optional[str]
    x_forwarded_for: Optional[str]
    x_real_ip: Optional[str]
    detected_real_ip: Optional[str]