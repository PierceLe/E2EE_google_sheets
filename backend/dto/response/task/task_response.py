from pydantic import BaseModel
from datetime import datetime

class TaskResponse(BaseModel):
    task_id: str
    room_id: str
    task_name: str
    task_description: str
    assigner_id: str
    assignee_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
