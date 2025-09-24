from typing import Optional, List
from sqlalchemy import and_
from database import get_db
from model.friend_draft import FriendDraft
from model.user import User



class FriendDraftRepository():
    def __init__(self):
        self.db = next(get_db())  # Call get_db() to get the session

    def find_by_user_id_and_friend_id(self, user_id: str, friend_id: str) -> FriendDraft:
        db_friend_draft = self.db.query(FriendDraft).filter(FriendDraft.user_id == user_id, FriendDraft.friend_id == friend_id).first()
        return db_friend_draft
    
    def save(self, friend_draft: FriendDraft) -> FriendDraft:
        self.db.add(friend_draft)
        self.db.commit()
        self.db.refresh(friend_draft)
        return friend_draft
    
    def delete_by_user_id_and_friend_id(self, user_id: str, friend_id: str):
        self.db.query(FriendDraft).filter(FriendDraft.user_id == user_id, FriendDraft.friend_id == friend_id).delete()
        self.db.commit()

    def get_user_send_request_add_friend(self, user_id:str):
        query = self.db.query(User)
        query = query.join(FriendDraft, and_(User.user_id == FriendDraft.user_id, FriendDraft.friend_id == user_id))
        query = query.order_by(FriendDraft.updated_at.desc())
        return query.all()
    
    def get_user_send_request_add_friend_pagging(self, user_id: str, page: int, page_size: int):
        query = self.db.query(User)
        query = query.join(FriendDraft, and_(User.user_id == FriendDraft.user_id, FriendDraft.friend_id == user_id))
        total = query.count()
        query = query.order_by(FriendDraft.updated_at.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        items = query.all()
        total_pages = (total + page_size - 1) // page_size
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def get_user_received_request_add_friend_from_user_id(self, user_id:str):
        query = self.db.query(User)
        query = query.join(FriendDraft, and_(User.user_id == FriendDraft.friend_id, FriendDraft.user_id == user_id))
        query = query.order_by(FriendDraft.updated_at.desc())
        return query.all() 