from database import SessionLocal
from model.user import User

class UserRepository:
    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        avatar_url: str,
    ) -> User:
        with SessionLocal() as db:
            db_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                avatar_url=avatar_url,
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
                first_name=first_name,
                last_name=last_name,
                avatar_url=avatar_url,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user

    def get_user_by_id(self, user_id: str) -> User:
        with SessionLocal() as db:
            return db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_email(self, email: str) -> User:
        with SessionLocal() as db:
            query = db.query(User).filter(User.email == email)
            db_user = query.first()
            if db_user:
                db.refresh(db_user)
            return db_user

    def check_user_exist_by_email(self, email: str) -> bool:
        with SessionLocal() as db:
            query = db.query(User).filter(User.email == email)
            return query.first() is not None


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

