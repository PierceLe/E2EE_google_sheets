from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from service.user_service import UserService
from utils.oauth_cookie import OAuth2PasswordBearerWithCookie
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from config import app_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="login")


class AuthService():
    def __init__(self):
        self.user_service = UserService()


    def create_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + \
            timedelta(minutes=app_config["AUTHENTICATION"]["ACCESS_TOKEN_EXPIRE_MINUTES_LOGIN"])

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            app_config["AUTHENTICATION"]["SECRET_KEY_LOGIN"],
            algorithm=app_config["AUTHENTICATION"]["ALGORITHM"])
        return encoded_jwt

    
    def login_or_create_google_user(self, token: str):
        try:
            idinfo = id_token.verify_oauth2_token(token, Request(), app_config["GOOGLE_AUTHENTICATION"]["CLIENT_ID"])
            email = idinfo["email"]
            first_name = idinfo.get("given_name")
            last_name = idinfo.get("family_name")
            avatar_url = idinfo.get("picture")
            
            user = self.user_service.get_user_by_email(email)
            if user:
                return user

            new_user = self.user_service.create_user_google(email=email, first_name=first_name,
                            last_name=last_name, avatar_url=avatar_url)
            return new_user
        except ValueError as e:
            print(e)
            raise AppException(ErrorCode.INVALID_GOOGLE_TOKEN)


    def check_token(self, token: str):
        try:
            payload = jwt.decode(
                token, app_config["AUTHENTICATION"]["SECRET_KEY_LOGIN"], algorithms=[
                    app_config["AUTHENTICATION"]["ALGORITHM"]])
            email = payload["sub"]
            if email is None:
                raise AppException(ErrorCode.UNAUTHORIZED)
        except JWTError:
            raise AppException(ErrorCode.UNAUTHORIZED)

        user = self.user_service.get_user_by_email(email, get_use_2fa_login=True)
        if user is None:
            raise AppException(ErrorCode.UNAUTHORIZED)
        return user