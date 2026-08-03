from pydantic import BaseModel, Field


class LinkTelegramRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    access_token: str = Field(min_length=1)
    token_type: str = "bearer"
