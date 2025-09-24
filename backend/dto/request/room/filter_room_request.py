from typing import Optional, List

from fastapi import Query

from dto.request.base_page_request import BasePageRequest
from enums.enum_room_type import E_Room_Type


class FilterRoomRequest(BasePageRequest):
    room_name: Optional[str] = Query(None)
    room_type: Optional[E_Room_Type] = None
    user_id: Optional[str] = None
