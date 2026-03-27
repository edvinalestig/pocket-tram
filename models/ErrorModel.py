from typing import Optional
from pydantic import BaseModel

class ErrorModel(BaseModel):
    errorCode: Optional[int]
    errorMessage: Optional[str]
