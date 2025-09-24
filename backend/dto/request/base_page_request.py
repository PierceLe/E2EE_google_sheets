from typing import Optional, List

from fastapi import Query
from pydantic import BaseModel


class BasePageRequest(BaseModel):
    page: int = Query(default=1, ge=1)
    page_size: int = Query(default=100, ge=1, le=100)
    # sort_by: Optional[str] = Query(None)
    sorts_by: Optional[List[str]] = Query(None)
    sorts_dir: Optional[List[str]] = Query(None)
