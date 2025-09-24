from pydantic import BaseModel

class LoginResponse(BaseModel):
    login_type: str 
    token: str

    class Config:
        from_attributes = True