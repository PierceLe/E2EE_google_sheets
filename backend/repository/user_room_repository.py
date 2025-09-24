from sqlalchemy import and_
from database import get_db
from model.user import User
from model.user_room import UserRoom


class UserRoomRepository():
    def __init__(self):
        self.db = next(get_db())

    def create_user_room(self,
                         user_id: str,
                         room_id: str,
                         encrypted_group_key: str
                         ) -> UserRoom:
        db_user_room = UserRoom(
            user_id=user_id,
            room_id=room_id,
            encrypted_group_key = encrypted_group_key
        )
        self.db.add(db_user_room)
        self.db.commit()
        self.db.refresh(db_user_room)

        return db_user_room

    def check_exist_by_user_id_and_room_id(self, user_id: str, room_id: str):
        user_room = self.db.query(UserRoom).filter(and_(UserRoom.user_id == user_id, UserRoom.room_id == room_id)).first()
        return user_room is not None

    def delete_user_room_by_user_id_and_room_id(self, user_id: str, room_id: str):
        db_user_room = self.db.query(UserRoom).filter(and_(UserRoom.user_id == user_id, UserRoom.room_id == room_id)).first()
        if db_user_room:
            self.db.delete(db_user_room)
            self.db.commit()

    def get_user_in_room(self, room_id: str):
        query = self.db.query(User)
        query = query.join(UserRoom, and_(User.user_id == UserRoom.user_id, UserRoom.room_id == room_id))
        query = query.order_by(User.email.asc())
        return query.all()
    
    def get_room_of_user(self, user_id: str):
        rooms = self.db.query(UserRoom.room_id).filter(UserRoom.user_id == user_id).all()
    
        # Return list room_id
        return [room.room_id for room in rooms]

    
    def delete_user_room_by_room_id(self, room_id: str):
        self.db.query(UserRoom).filter(UserRoom.room_id == room_id).delete()
        self.db.commit()

    def delete_user_room_by_room_id_and_list_user_id(self, room_id: str, list_user_id: list = []):
        self.db.query(UserRoom).filter(and_(UserRoom.room_id == room_id, UserRoom.user_id.in_(list_user_id))).delete()
        self.db.commit()

    def save_all(self, list_user_room : list[UserRoom]):
        self.db.bulk_save_objects(list_user_room)
        self.db.commit()

    def get_user_room_by_user_id_and_room_id(self, user_id: str, room_id: str):
        db_user_room = self.db.query(UserRoom).filter(and_(UserRoom.user_id == user_id, UserRoom.room_id == room_id)).first()
        return db_user_room