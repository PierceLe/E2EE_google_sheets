import smtplib
import pyotp
import qrcode
import base64
from io import BytesIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import app_config
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from service.user_service import UserService
from utils.oauth_cookie import OAuth2PasswordBearerWithCookie
from fastapi import Depends, HTTPException, status
from dto.request.auth.user_create_request import UserCreateRequest
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from dto.response.user_response import UserResponse
from googleapiclient.discovery import build
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from config import app_config
from enums.enum_login_method import E_Login_Method

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="login")


class AuthService():
    def __init__(self):
        self.user_service = UserService()

    def signup(self, user_create: UserCreateRequest):
        existing_user = self.user_service.get_user_by_email(
            user_create.email, only_verified=False)

        # If user is existed and email is verified then prevent creating user
        if existing_user and existing_user.is_verified:
            raise AppException(ErrorCode.USER_EXISTED)

        # If user is existed but email is not verified then delete it first
        if existing_user and not existing_user.is_verified:
            is_deleted = self.user_service.delete_user_by_email(
                user_create.email)
            if not is_deleted:
                raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION)

        # Create new record and send email verification

        user = self.user_service.create_user(user_create)

        access_token_signup = self.create_email_verification_token(
            data={"sub": user_create.email})
        self.send_email_token_signup(
            email=user_create.email,
            verification_token=access_token_signup)

        return user

    def forgot_password(self, email):
        existing_user = self.user_service.get_user_by_email(
            email, only_verified=True)

        # If user is not existed then raise error
        if not existing_user:
            raise AppException(ErrorCode.USER_NOT_FOUND)

        # In the remaining cases, send an email with a token to the user to
        # confirm the password reset action.
        access_token_reset_password = self.create_email_verification_token(data={
                                                                           "sub": email})
        self.send_email_token_reset_password(
            email=email,
            verification_token=access_token_reset_password,
            user=existing_user)

        return existing_user

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

    def create_email_verification_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + \
            timedelta(minutes=app_config["AUTHENTICATION"]["ACCESS_TOKEN_EXPIRE_MINUTES_EMAIL_VERIFICATION"])

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            app_config["AUTHENTICATION"]["SECRET_KEY_EMAIL_VERIFICATION"],
            algorithm=app_config["AUTHENTICATION"]["ALGORITHM"])
        return encoded_jwt

    def create_2fa_verification_token(self, data:dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + \
            timedelta(minutes=app_config["AUTHENTICATION"]["ACCESS_TOKEN_EXPIRE_MINUTES_2FA_VERIFICATION"])

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            app_config["AUTHENTICATION"]["SECRET_KEY_2FA_VERIFICATION"],
            algorithm=app_config["AUTHENTICATION"]["ALGORITHM"])
        return encoded_jwt

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, email: str, password: str, get_full_info: bool = False):
        user = self.user_service.get_user_by_email(email, get_full_info=get_full_info)
        if not user:
            return False
        if not self.verify_password(
            password, self.user_service.get_password(
                user.user_id)):
            return False
        return user
    
    def login_or_create_google_user(self, token: str):
        try:
            idinfo = id_token.verify_oauth2_token(token, Request(), app_config["GOOGLE_AUTHENTICATION"]["CLIENT_ID"])
            email = idinfo["email"]
            name = idinfo.get("name")
            first_name = idinfo.get("given_name")
            last_name = idinfo.get("family_name")
            avatar_url = idinfo.get("picture")
            
            user = self.user_service.get_user_by_email(email, get_full_info=True)
            if user:
                if user.method == E_Login_Method.NORMAL:
                    raise AppException(ErrorCode.INVALID_METHOD_LOGIN)
                else:
                    return user

            new_user = self.user_service.create_user_google(email=email, first_name=first_name, 
                            last_name=last_name, avatar_url=avatar_url)

            return new_user
        except ValueError as e:
            print(e)
            raise AppException(ErrorCode.INVALID_GOOGLE_TOKEN)


    def update_user_verified(self, email: str, is_verified=True):
        user = self.user_service.get_user_by_email(email, only_verified=False)
        if not user:
            raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION)

        return self.user_service.update_user_verified_by_email(
            email, is_verified=is_verified)

    def update_password(self, user_id, new_password):
        return self.user_service.update_password(user_id, new_password)

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

    def check_email_verification_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                app_config["AUTHENTICATION"]["SECRET_KEY_EMAIL_VERIFICATION"],
                algorithms=[
                    app_config["AUTHENTICATION"]["ALGORITHM"]])
            email = payload["sub"]
            if email is None:
                raise AppException(ErrorCode.EMAIL_VERIFICATION_FAILED)
        except JWTError:
            raise AppException(ErrorCode.EMAIL_VERIFICATION_FAILED)

        user = self.user_service.get_user_by_email(email, only_verified=False)
        if user is None:
            raise AppException(ErrorCode.USER_NOT_FOUND)
        return user
    
    def check_2fa_verification_token(self, token: str, code: str):
        try:
            payload = jwt.decode(
                token,
                app_config["AUTHENTICATION"]["SECRET_KEY_2FA_VERIFICATION"],
                algorithms=[
                    app_config["AUTHENTICATION"]["ALGORITHM"]])
            email = payload["sub"]
            if email is None:
                raise AppException(ErrorCode.TWOFA_VERIFICATION_FAILED)
        except JWTError:
            raise AppException(ErrorCode.TWOFA_VERIFICATION_FAILED)

        user = self.user_service.get_user_by_email(email, only_verified=False, get_full_info=True)
        if user is None:
            raise AppException(ErrorCode.USER_NOT_FOUND)
        
        if not user.two_factor_secret:
            raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION)
        
        # Check if the user entered code is correct
        totp = pyotp.TOTP(user.two_factor_secret)
        otp = totp.now()
        if (otp != code):
            raise AppException(ErrorCode.CODE_2FA_WRONG)

        return user

    def send_email_token_signup(
            self,
            email: str,
            verification_token: str) -> str:
        verification_url = "{0}/verify-email-signup?token={1}".format(
            app_config["WEB"]["FRONTEND"]["DOMAIN"], verification_token)
        html_body = f"""
            <html>
                <body>
                    <p>Click the link below to verify your email address for signup:</p>
                    <p><a href="{verification_url}">Click here to verify your email</a></p>
                    <p>If you did not request this, please ignore this email.</p>
                </body>
            </html>
        """
        self.send_email(
            sender_email=app_config["APP_EMAIL"]["SENDER"],
            receiver_email=email,
            subject="Verify your email address for signup",
            html_body=html_body,
            smtp_server=app_config["APP_EMAIL"]["SMTP_SERVER"],
            smtp_port=app_config["APP_EMAIL"]["SMTP_PORT"],
            password_google_app=app_config["APP_EMAIL"]["PASSWORD"]
        )

    def send_email_token_reset_password(
            self,
            email: str,
            verification_token: str,
            user: UserResponse) -> str:
        verification_url = "{0}/reset-password?token={1}".format(
            app_config["WEB"]["FRONTEND"]["DOMAIN"], verification_token)
        html_body = f"""
            <html>
                <body>
                    <p>Dear {user.first_name} {user.last_name},</p>
                    <p>Click the link below to confirm your password reset:</p>
                    <p><a href="{verification_url}">Click here to reset your password</a></p>
                    <p>If you did not request this change, please ignore this email.</p>
                    <p>Best regards,</p>
                </body>
            </html>
            """

        self.send_email(
            sender_email=app_config["APP_EMAIL"]["SENDER"],
            receiver_email=email,
            subject="Verify password reset",
            html_body=html_body,
            smtp_server=app_config["APP_EMAIL"]["SMTP_SERVER"],
            smtp_port=app_config["APP_EMAIL"]["SMTP_PORT"],
            password_google_app=app_config["APP_EMAIL"]["PASSWORD"]
        )

    def send_email(
            self,
            sender_email: str,
            receiver_email: str,
            subject: str,
            html_body: str,
            smtp_server: str,
            smtp_port: int,
            password_google_app: str):
        """Send email by using SMTP."""
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Add more content for email
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, password_google_app)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, msg.as_string())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            server.quit()
    
    def enable_2fa(self, user_id):
        print("Enabling 2FA")
        user_full = self.user_service.get_user(user_id=user_id, get_full_info=True)

        if user_full.use_2fa_login:
            raise AppException(ErrorCode.ACCOUNT_USED_2FA)

        print("Generate QR Code")
        # Generate 2FA secret and provisioning URI
        two_factor_secret = pyotp.random_base32()
        uri = pyotp.TOTP(two_factor_secret).provisioning_uri(
            name=user_full.email,
            issuer_name=app_config["APP_GENERAL"]["APP_NAME"]
        )

        print(f"URI: {uri}")
        # Generate QR code image
        qr = qrcode.make(uri)
        img_io = BytesIO()
        qr.save(img_io, format="PNG")
        img_io.seek(0)

        print(f"QR code: {qr}")
        # Convert to base64 string
        qr_base64 = base64.b64encode(img_io.read()).decode("utf-8")
        # Save secret to DB
        self.user_service.update_two_factor_secret(user_id, two_factor_secret)

        # Return base64 string
        return qr_base64
    
    def disable_2fa(self, user_id: str):
        self.user_service.disable_2fa(user_id)


        
        
        

        
