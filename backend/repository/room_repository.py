from typing import Optional, List

from sqlalchemy import and_, or_

from database import get_db
from model.room import Room
from enums.enum_room_type import E_Room_Type
from model.user import User
from model.user_room import UserRoom
from sqlalchemy.orm import aliased



class RoomRepository():
    def __init__(self):
        self.db = next(get_db())  # Call get_db() to get the session

    def create_room(self,
                    room_name: str,
                    creator_id: str,
                    room_type: E_Room_Type,
                    avatar_url: str,
                    description: str
                    ) -> Room:
        db_room = Room(
            room_name=room_name,
            creator_id=creator_id,
            room_type=room_type,
            avatar_url=avatar_url,
            description=description
        )
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        return db_room

    def get_room_by_room_id(self, room_id: str) -> Room:
        db_room = self.db.query(Room).filter(Room.room_id == room_id).first()
        return db_room

    def save(self, room: Room) -> Room:
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_rooms_filter(self,
                        room_name: Optional[str],
                        user_id: str,
                        room_type: E_Room_Type,
                        page: int,
                        page_size: int,
                        sorts_by: Optional[List[str]],
                        sorts_dir: Optional[List[str]]
                         ):
        query = self.db.query(Room, User, UserRoom.encrypted_group_key.label('encrypted_group_key'))

        if room_name is not None:
            query = query.filter(Room.room_name.ilike(f"%{room_name}%"))
        
        if room_type is not None:
            query = query.filter(Room.room_type == room_type)
        
        query = query.join(UserRoom, and_(Room.room_id == UserRoom.room_id, UserRoom.user_id == user_id))

        query = query.outerjoin(User, Room.last_sender_id == User.user_id)

        total = query.count()

        if sorts_by:
            for sort_by, sort_dir in zip(sorts_by, sorts_dir):
                sort_column = getattr(Room, sort_by)
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

    def check_exist_room_by_room_id(self, room_id: str) -> bool:
        room_db = self.db.query(Room).filter(Room.room_id == room_id).first()
        return room_db is not None

    def delete_room_by_id(self, room_id):
        self.db.query(Room).filter(Room.room_id == room_id).delete()
        self.db.commit()

    def get_rooms_one_filter(
            self, 
            friend_name: Optional[str],
            user_id: str,
            page: int,
            page_size: int,
            sorts_by: Optional[List[str]],
            sorts_dir: Optional[List[str]]
        ):

        ur1 = aliased(UserRoom)
        ur2 = aliased(UserRoom)

        u1 = aliased(User)

        query = self.db.query(Room, 
            u1,
            User.user_id.label('friend_id'), 
            User.email.label('friend_email'),
            User.first_name.label('friend_frist_name'),
            User.last_name.label('friend_last_name'),
            User.avatar_url.label('friend_avatar_url'),
            ur1.encrypted_group_key.label('encrypted_group_key')
            )
        
        query = query.outerjoin(u1, Room.last_sender_id == u1.user_id)

        query = query.join(ur1, 
                   and_(
                    Room.room_type == E_Room_Type.ONE, 
                    Room.room_id == ur1.room_id,
                    ur1.user_id == user_id
                    )
            ).join(ur2, 
                   and_(
                    ur2.room_id == ur1.room_id,
                    ur2.id != ur1.id
                   )
            ).join(User, 
                   and_(
                    ur2.user_id == User.user_id,
                    or_(
                        User.first_name.ilike(f"%{friend_name}%"),
                        User.last_name.ilike(f"%{friend_name}%")
                    )
                )
            ).order_by(User.first_name.asc(), User.last_name.asc())
        
        

        total = query.count()
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
    
    def update_last_message_in_room(self, room_id: str, message: str, last_sender_id: str):
        self.db.query(Room).filter(Room.room_id == room_id).update({"last_mess": message, "last_sender_id": last_sender_id})
        self.db.commit()

    def is_exits_chat_one_one(self, user1_id: str, user2_id: str):
        ur1 = aliased(UserRoom)
        ur2 = aliased(UserRoom)

        count = self.db.query(Room, 
            User.user_id.label('friend_id'), 
            User.email.label('friend_email'),
            User.first_name.label('friend_frist_name'),
            User.last_name.label('friend_last_name'),
            User.avatar_url.label('friend_avatar_url')
            ).join(ur1, 
                   and_(
                    Room.room_type == E_Room_Type.ONE, 
                    Room.room_id == ur1.room_id,
                    ur1.user_id == user1_id
                    )
            ).join(ur2, 
                   and_(
                    ur2.room_id == ur1.room_id,
                    ur2.id != ur1.id
                   )
            ).join(User, 
                   and_(
                    ur2.user_id == User.user_id,
                    ur2.user_id == user2_id
                    )
                ).count()
        
        return count >= 1


    def find_chat_one_one(self, user1_id: str, user2_id: str):
        ur1 = aliased(UserRoom)
        ur2 = aliased(UserRoom)

        result = self.db.query(
            Room.room_id,
            User.user_id.label('friend_id'),
            User.email.label('friend_email'),
            User.first_name.label('friend_first_name'),
            User.last_name.label('friend_last_name'),
            User.avatar_url.label('friend_avatar_url')
            ).join(ur1,
                   and_(
                       Room.room_type == E_Room_Type.ONE,
                       Room.room_id == ur1.room_id,
                       ur1.user_id == user1_id
                   )
           ).join(ur2,
                  and_(
                      ur2.room_id == ur1.room_id,
                      ur2.id != ur1.id
                  )
           ).join(User,
                 and_(
                     ur2.user_id == User.user_id,
                     ur2.user_id == user2_id
                 )
            ).first()

        return result[0] if result else None
    
    def get_room_one_has_user_id(self, user_id):
        query = self.db.query(Room).filter(Room.room_type == E_Room_Type.ONE)
        query = query.join(UserRoom, and_(Room.room_id == UserRoom.room_id, UserRoom.user_id == user_id))
        return query.all()

