from typing import List, Optional
from fastapi import HTTPException, Request, status
from model.user import User

async def get_current_user(request: Request) -> User:
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return request.state.user


def pagging_query(page: int,
                  page_size: int,
                  sorts_by: Optional[List[str]],
                  sorts_dir: Optional[List[str]],
                  classModel,
                  query
                  ):

    total = query.count()

    if sorts_by:
        for sort_by, sort_dir in zip(sorts_by, sorts_dir):
            sort_colum = getattr(classModel, sort_by)
            if sort_dir == "desc":
                query = query.order_by(sort_colum.desc())
            else:
                query = query.order_by(sort_colum.asc())

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