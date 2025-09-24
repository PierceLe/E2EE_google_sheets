from pydantic import BaseModel, constr, validator

class LoginRequest(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True