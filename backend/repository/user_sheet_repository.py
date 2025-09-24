from typing import List, Optional
from sqlalchemy import and_
from database import get_db
from model.user import User
from model.user_sheet import UserSheet


class UserSheetRepository:
    def __init__(self):
        self.db = next(get_db())

    def create_user_sheet(
            self,
            user_id: str,
            sheet_id: str,
            encrypted_sheet_key: str,
            role: str = "viewer",
            is_favorite: bool = False
    ) -> UserSheet:
        if not encrypted_sheet_key or not encrypted_sheet_key.strip():
            raise ValueError("encrypted_sheet_key is required and cannot be empty")

        db_user_sheet = UserSheet(
            user_id=user_id,
            sheet_id=sheet_id,
            role=role,
            encrypted_sheet_key=encrypted_sheet_key,
            is_favorite=is_favorite
        )
        self.db.add(db_user_sheet)
        self.db.commit()
        self.db.refresh(db_user_sheet)
        return db_user_sheet

    def check_exist_by_user_id_and_sheet_id(self, user_id: str, sheet_id: str) -> bool:
        return (
                self.db.query(UserSheet)
                .filter(and_(UserSheet.user_id == user_id, UserSheet.sheet_id == sheet_id))
                .first()
                is not None
        )

    def delete_user_sheet_by_user_id_and_sheet_id(self, user_id: str, sheet_id: str) -> None:
        row = (
            self.db.query(UserSheet)
            .filter(and_(UserSheet.user_id == user_id, UserSheet.sheet_id == sheet_id))
            .first()
        )
        if row:
            self.db.delete(row)
            self.db.commit()

    def get_user_in_sheet(self, sheet_id: str) -> List[User]:
        query = self.db.query(User)
        query = query.join(
            UserSheet,
            and_(User.user_id == UserSheet.user_id, UserSheet.sheet_id == sheet_id)
        )
        return query.order_by(User.email.asc()).all()

    def get_sheet_of_user(self, user_id: str) -> List[str]:
        rows = self.db.query(UserSheet.sheet_id).filter(UserSheet.user_id == user_id).all()
        return [row.sheet_id for row in rows]

    def delete_user_sheet_by_sheet_id(self, sheet_id: str) -> None:
        self.db.query(UserSheet).filter(UserSheet.sheet_id == sheet_id).delete()
        self.db.commit()

    def delete_user_sheet_by_sheet_id_and_list_user_id(self, sheet_id: str, list_user_id: list[str]) -> None:
        self.db.query(UserSheet).filter(
            and_(UserSheet.sheet_id == sheet_id, UserSheet.user_id.in_(list_user_id))
        ).delete(synchronize_session=False)
        self.db.commit()

    def save_all(self, list_user_sheet: list[UserSheet]) -> None:
        for us in list_user_sheet:
            if not us.encrypted_sheet_key or not us.encrypted_sheet_key.strip():
                raise ValueError("encrypted_sheet_key is required for all UserSheet items")
        self.db.bulk_save_objects(list_user_sheet)
        self.db.commit()

    def get_user_sheet_by_user_id_and_sheet_id(self, user_id: str, sheet_id: str) -> Optional[UserSheet]:
        return (
            self.db.query(UserSheet)
            .filter(and_(UserSheet.user_id == user_id, UserSheet.sheet_id == sheet_id))
            .first()
        )

    # --- Extra helpers ---
    def update_encrypted_key(self, user_id: str, sheet_id: str, new_encrypted_key: str) -> bool:
        if not new_encrypted_key or not new_encrypted_key.strip():
            raise ValueError("new_encrypted_key cannot be empty")

        row = (
            self.db.query(UserSheet)
            .filter(and_(UserSheet.user_id == user_id, UserSheet.sheet_id == sheet_id))
            .first()
        )
        if not row:
            return False
        row.encrypted_sheet_key = new_encrypted_key
        self.db.commit()
        self.db.refresh(row)
        return True

    def update_role(self, user_id: str, sheet_id: str, role: str) -> bool:
        row = (
            self.db.query(UserSheet)
            .filter(and_(UserSheet.user_id == user_id, UserSheet.sheet_id == sheet_id))
            .first()
        )
        if not row:
            return False
        row.role = role
        self.db.commit()
        self.db.refresh(row)
        return True

    def mark_favorite(self, user_id: str, sheet_id: str, is_favorite: bool) -> bool:
        row = (
            self.db.query(UserSheet)
            .filter(and_(UserSheet.user_id == user_id, UserSheet.sheet_id == sheet_id))
            .first()
        )
        if not row:
            return False
        row.is_favorite = is_favorite
        self.db.commit()
        self.db.refresh(row)
        return True