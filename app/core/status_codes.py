from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ResponseStatus(str, Enum):
    """Response status for API calls"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BaseResponse(BaseModel):
    """Base response model for all API endpoints"""
    status: ResponseStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    trace_id: Optional[str] = None


 