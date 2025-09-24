from pydantic import BaseModel, constr, validator

class Restore_Private_Key_Request(BaseModel):
    pin: str

    class Config:
        from_attributes = True