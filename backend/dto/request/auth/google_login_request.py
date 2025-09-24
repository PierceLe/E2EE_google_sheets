from pydantic import BaseModel, Field

class GoogleLoginRequest(BaseModel):
    """Request model for Google OAuth2 authentication"""
    
    token: str = Field(
        ...,
        description="Google OAuth2 access token obtained from Google's authorization server",
        example="ya29.a0ARrdaM9...",
        min_length=1
    )

    class Config:
        schema_extra = {
            "example": {
                "token": "ya29.a0ARrdaM9Y8K7X2Z1B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z"
            }
        }