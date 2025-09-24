from typing import Optional
from fastapi import Query
from dto.request.base_page_request import BasePageRequest


class FilterSheetRequest(BasePageRequest):
    user_id: Optional[str] = None
    is_favorite: Optional[bool] = Query(None)
    role: Optional[str] = Query(None)  # owner, editor, viewer

    class Config:
        from_attributes = True
