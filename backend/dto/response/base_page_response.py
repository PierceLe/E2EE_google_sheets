from typing import List, Any

from pydantic import BaseModel


class BasePageResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int