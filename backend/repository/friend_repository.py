from typing import Optional, List
from sqlalchemy import and_, or_
from database import get_db
from model.friend import Friend
from model.user import User



class FriendRepository():
    def __init__(self):
        self.db = next(get_db())  # Call get_db() to get the session

    def is_friend(self, user_id: str, friend_id: str) -> bool:
        db_friend = self.db.query(Friend).filter(
            or_(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
                )
            ).first()
        return db_friend is not None
    
    def save(self, friend: Friend) -> Friend:
        self.db.add(friend)
        self.db.commit()
        self.db.refresh(friend)
        return friend
    
    def save_all(self, friends: List[Friend]):
        self.db.bulk_save_objects(friends)
        self.db.commit()

    def delete_by_user_id_and_friend_id(self, user_id: str, friend_id: str):
        self.db.query(Friend).filter(Friend.user_id == user_id, Friend.friend_id == friend_id).delete()
        self.db.commit()

    def delete_by_2_user_id(self, user_id: str, friend_id: str):
        self.db.query(Friend).filter(or_(
            and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
            and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
        )).delete()
        self.db.commit()

    def get_all_friends(self, user_id: str):
        query = self.db.query(User)
        query = query.join(Friend, and_(User.user_id == Friend.friend_id, Friend.user_id == user_id))
        query = query.order_by(User.first_name.asc())
        return query.all()
    
    def get_friend_pagging_and_filter(self, 
                                    user_id: str,
                                    name: Optional[str],
                                    page: int,
                                    page_size: int,
                                    sorts_by: Optional[List[str]],
                                    sorts_dir: Optional[List[str]]
                                    ):
        query = self.db.query(User)

        if name is not None:
            query = query.filter(or_(
                User.first_name.ilike(f"%{name}%"),
                User.last_name.ilike(f"%{name}%")
            ))

        query = query.join(Friend, and_(User.user_id == Friend.friend_id, Friend.user_id == user_id))

        total = query.count()
        if sorts_by:
            for sort_by, sort_dir in zip(sorts_by, sorts_dir):
                sort_column = getattr(User, sort_by)
                if sort_dir == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())

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

        