from sqlalchemy.orm import Session
from database import SessionLocal
from model.task import Task
from typing import List, Optional

class TaskRepository:
    def create_task(
        self,
        room_id: str,
        task_name: str,
        task_description: str,
        assigner_id: str,
        assignee_id: str,
        status: str
    ) -> Task:
        with SessionLocal() as db:
            db_task = Task(
                room_id=room_id,
                task_name = task_name,
                task_description = task_description,
                assigner_id = assigner_id,
                assignee_id = assignee_id,
                status=status
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            return db_task

    def get_task_by_id(self, task_id: str) -> Task:
        with SessionLocal() as db:
            return db.query(Task).filter(Task.task_id == task_id).first()

    def get_list_task_by_room_id(self, room_id: str) -> List[Task]:
        with SessionLocal() as db:
            return (
                db.query(Task)
                .filter(Task.room_id == room_id)
                .order_by(Task.created_at)
                .all()
            )

    def update_task_status(self, task_id: str, status: str) -> Optional[Task]:
        with SessionLocal() as db:
            db_task = db.query(Task).filter(Task.task_id == task_id).first()
            if db_task:
                db_task.status = status
                db.commit()
                db.refresh(db_task)
                return db_task
            return None

    def delete_task(self, task_id: str) -> bool:
        with SessionLocal() as db:
            db_task = db.query(Task).filter(Task.task_id == task_id).first()
            if db_task:
                db.delete(db_task)
                db.commit()
                return True
            return False
