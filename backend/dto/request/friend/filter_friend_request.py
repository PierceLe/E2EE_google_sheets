from typing import Optional, List

from fastapi import Query

from dto.request.base_page_request import BasePageRequest


class FilterFriendRequest(BasePageRequest):
    name: Optional[str] = Query(None)
    user_id: Optional[str] = None