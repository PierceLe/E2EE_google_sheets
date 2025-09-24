from pydantic import BaseModel, constr, validator

class Check2FARequest(BaseModel):
    token: str
    code: str

    class Config:
        from_attributes = True