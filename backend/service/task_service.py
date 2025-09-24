from repository.task_repository import TaskRepository
from dto.response.task.task_response import TaskResponse
from dto.request.task.create_task_request import TaskCreateRequest
from typing import List
from repository.user_room_repository import UserRoomRepository
from repository.room_repository import RoomRepository

class TaskService():
    def __init__(self):
        self.task_repository = TaskRepository()
        self.user_room_repository = UserRoomRepository()
        self.room_repository = RoomRepository()

    def create_task(self, task_request: TaskCreateRequest, current_user_id: str) -> TaskResponse:
        room = self.room_repository.get_room_by_room_id(task_request.room_id)
        if room is None:
            raise AppException(ErrorCode.ROOM_NOT_FOUND)
        if not self.user_room_repository.check_exist_by_user_id_and_room_id(current_user_id, task_request.room_id):
            raise AppException(ErrorCode.NOT_PERMISSION)

        task = self.task_repository.create_task(
            room_id = task_request.room_id,
            task_name = task_request.task_name,
            task_description = task_request.task_description,
            assigner_id = task_request.assigner_id,
            assignee_id = task_request.assignee_id,
            status = task_request.status
        )

        return TaskResponse(
            task_id = task.task_id,
            room_id = task.room_id,
            task_name = task.task_name,
            task_description = task.task_description,
            assigner_id = task.assigner_id,
            assignee_id = task.assignee_id,
            status = task.status,
            created_at = task.created_at,
            updated_at = task.updated_at
        )
    
    def get_task_by_id(self, task_id: str, current_user_id: str) -> TaskResponse:
        task = self.task_repository.get_task_by_id(task_id=task_id)

        if not task:
            return None
        
        room = self.room_repository.get_room_by_room_id(task.room_id)
        if room is None:
            raise AppException(ErrorCode.ROOM_NOT_FOUND)
        if not self.user_room_repository.check_exist_by_user_id_and_room_id(current_user_id, task.room_id):
            raise AppException(ErrorCode.NOT_PERMISSION)

        return TaskResponse(
            task_id = task.task_id,
            room_id = task.room_id,
            task_name = task.task_name,
            task_description = task.task_description,
            assigner_id = task.assigner_id,
            assignee_id = task.assignee_id,
            status = task.status,
            created_at = task.created_at,
            updated_at = task.updated_at
        )
    
    def get_list_task_by_room_id(self, room_id: str, current_user_id: str) -> List[TaskResponse]:
        room = self.room_repository.get_room_by_room_id(room_id)
        if room is None:
            raise AppException(ErrorCode.ROOM_NOT_FOUND)
        if not self.user_room_repository.check_exist_by_user_id_and_room_id(current_user_id,room_id):
            raise AppException(ErrorCode.NOT_PERMISSION)

        list_tasks = self.task_repository.get_list_task_by_room_id(room_id)
        if not list_tasks:
            return None
        
        return [
            TaskResponse(
                task_id = task.task_id,
                room_id=task.room_id,
                task_name=task.task_name,
                task_description=task.task_description,
                assigner_id=task.assigner_id,
                assignee_id=task.assignee_id,
                status=task.status,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in list_tasks
    ]

    def update_task_status(self, task_id: str, status: str, current_user_id: str) -> TaskResponse:
        task = self.task_repository.update_task_status(task_id, status)
        if not task:
            return None
        
        room = self.room_repository.get_room_by_room_id(task.room_id)
        if room is None:
            raise AppException(ErrorCode.ROOM_NOT_FOUND)
        if not self.user_room_repository.check_exist_by_user_id_and_room_id(current_user_id, task.room_id):
            raise AppException(ErrorCode.NOT_PERMISSION)

        return TaskResponse(
            task_id = task.task_id,
            room_id = task.room_id,
            task_name = task.task_name,
            task_description = task.task_description,
            assigner_id = task.assigner_id,
            assignee_id = task.assignee_id,
            status = task.status,
            created_at = task.created_at,
            updated_at = task.updated_at
        )

    
    def delete_task_by_id(self, task_id: str, current_user_id: str):
        task = self.task_repository.get_task_by_id(task_id=task_id)
        if not task:
            return None
        
        room = self.room_repository.get_room_by_room_id(task.room_id)
        if room is None:
            raise AppException(ErrorCode.ROOM_NOT_FOUND)
        if not self.user_room_repository.check_exist_by_user_id_and_room_id(current_user_id, task.room_id):
            raise AppException(ErrorCode.NOT_PERMISSION)

        return self.task_repository.delete_task(task_id)

