from pydantic import BaseModel, Field, validator

class Create_Pin_Request(BaseModel):
    """Request model for setting up user PIN and RSA key pair"""
    
    pin: str = Field(
        ...,
        description="User's PIN for private key encryption (hashed client-side)",
        example="hashed_pin_value",
        min_length=1
    )
    public_key: str = Field(
        ...,
        description="RSA public key in PEM format for encrypting sheet keys",
        example="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
        min_length=1
    )
    encrypted_private_key: str = Field(
        ...,
        description="RSA private key encrypted with user's PIN",
        example="U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt...",
        min_length=1
    )

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "pin": "hashed_pin_12345",
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
                "encrypted_private_key": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt"
            }
        }