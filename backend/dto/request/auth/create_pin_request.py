from pydantic import BaseModel, constr, validator

class Create_Pin_Request(BaseModel):
    pin: str
    public_key: str
    encrypted_private_key: str

    class Config:
        from_attributes = True