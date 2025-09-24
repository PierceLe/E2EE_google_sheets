from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from model.sheet import Sheet


class SheetRepository:
    def create_sheet(self, link: str, creator_id: str) -> Sheet:
        """
        Create a new sheet and return the persisted entity (with generated sheet_id).
        """
        with SessionLocal() as db:
            sheet = Sheet(link=link, creator_id=creator_id)
            db.add(sheet)
            db.commit()
            db.refresh(sheet)
            return sheet

    def get_link_by_sheet_id(self, sheet_id: str) -> Optional[str]:
        """
        Return the sheet link for a given sheet_id. None if not found.
        """
        with SessionLocal() as db:  # type: Session
            row = db.query(Sheet.link).filter(Sheet.sheet_id == sheet_id).first()
            return row[0] if row else None