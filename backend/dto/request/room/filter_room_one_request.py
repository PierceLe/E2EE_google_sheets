from typing import Optional, List

from fastapi import Query

from dto.request.base_page_request import BasePageRequest


class FilterRoomOneRequest(BasePageRequest):
    friend_name: Optional[str] = Query('')
    user_id: Optional[str] = None
