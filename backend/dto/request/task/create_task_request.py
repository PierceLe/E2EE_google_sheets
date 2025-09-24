from pydantic import BaseModel

class TaskCreateRequest(BaseModel):
    room_id: str
    task_name: str
    task_description: str
    assigner_id: str
    assignee_id: str
    status: str

    class Config:
        from_attributes = True
