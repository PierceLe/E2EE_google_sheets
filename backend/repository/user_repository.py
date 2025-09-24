from sqlalchemy import and_
from sqlalchemy.orm import Session
from database import SessionLocal
from model.user import User
from dto.request.auth.user_update_request import UserUpdateRequest
from dto.request.auth.user_bio_update_request import UserBioUpdateRequest
from enums.enum_login_method import E_Login_Method

class UserRepository:
    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        avatar_url: str,
        is_verified: bool = False,
        use_2fa_login: bool = False,
        two_factor_secret: str = ""
    ) -> User:
        with SessionLocal() as db:
            db_user = User(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                avatar_url=avatar_url,
                is_verified=is_verified,
                use_2fa_login=use_2fa_login,
                two_factor_secret=two_factor_secret,
                method=E_Login_Method.NORMAL
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
    
    def create_user_google(
        self,
        email: str,
        first_name: str,
        last_name: str,
        avatar_url: str,
    ) -> User:
        with SessionLocal() as db:
            db_user = User(
                email=email,
                password="default_google",
                first_name=first_name,
                last_name=last_name,
                avatar_url=avatar_url,
                is_verified=True,
                use_2fa_login=False,
                method=E_Login_Method.GOOGLE
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user

    def get_user_by_id(self, user_id: str) -> User:
        with SessionLocal() as db:
            return db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_email(self, email: str, only_verified=True) -> User:
        with SessionLocal() as db:
            query = db.query(User).filter(User.email == email)
            if only_verified:
                query = query.filter(User.is_verified.is_(True))
            db_user = query.first()
            if db_user:
                db.refresh(db_user)
            return db_user

    def check_user_exist_by_email(self, email: str, only_verified=True) -> bool:
        with SessionLocal() as db:
            query = db.query(User).filter(User.email == email)
            if only_verified:
                query = query.filter(User.is_verified.is_(True))
            return query.first() is not None

    def update_user_verified_by_email(self, email: str, is_verified: bool) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.email == email).first()
            if db_user:
                db_user.is_verified = is_verified
                db.commit()
                db.refresh(db_user)
                return True
            return False

    def update_password(self, user_id: str, new_password: str) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                db_user.password = new_password
                db.commit()
                db.refresh(db_user)
                return True
            return False

    def update_two_factor_secret(self, user_id: str, two_factor_secret: str) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                db_user.use_2fa_login = True
                db_user.two_factor_secret = two_factor_secret
                db.commit()
                db.refresh(db_user)
                return True
            return False

    def update_user_info(self, user_id: str, user_update: UserUpdateRequest) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                update_data = user_update.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_user, key, value)
                db.commit()
                db.refresh(db_user)
                return True
            return False
    
    def update_user_bio(self, user_id: str, user_update: UserBioUpdateRequest) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                update_data = user_update.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_user, key, value)
                db.commit()
                db.refresh(db_user)
                return True
            return False

    def delete_user(self, user_id: str) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                db.delete(db_user)
                db.commit()
                return True
            return False

    def delete_user_by_email(self, email: str) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.email == email).first()
            if db_user:
                db.delete(db_user)
                db.commit()
                return True
            return False

    def disable_2fa(self, user_id: str) -> bool:
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                db_user.use_2fa_login = False
                db_user.two_factor_secret = ""
                db.commit()
                db.refresh(db_user)
                return True
            return False

    def create_pin(self, user_id: str, pin: str, public_key: str, encrypted_private_key: str):
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.user_id == user_id).first()
            if db_user:
                db_user.pin = pin
                db_user.public_key = public_key
                db_user.encrypted_private_key = encrypted_private_key
                db.commit()
                db.refresh(db_user)
                return True
            return False
        
    def query_by_email_not_in_list(self, list_user_id: list[str], email: str):
        with SessionLocal() as db:
            query = db.query(User)
            if email:
                query = query.filter(and_(~User.user_id.in_(list_user_id), User.email.ilike(f"%{email}%")))
            return query.all()

