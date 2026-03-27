from pydantic import BaseModel

class ErrorModel(BaseModel):
    errorCode: int
    errorMessage: str
