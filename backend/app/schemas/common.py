from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str

    model_config = ConfigDict(from_attributes=True)


class DatabaseHealthResponse(BaseModel):
    """Database connectivity health check response schema."""
    status: str
    database: str

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic status/message response schema."""
    message: str

    model_config = ConfigDict(from_attributes=True)
