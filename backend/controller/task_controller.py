from service.task_service import TaskService
from dto.request.task.create_task_request import TaskCreateRequest
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from dto.response.success_response import SuccessResponse
from utils.utils import get_current_user
from model.user import User

task_router = APIRouter()

@task_router.post("/create")
async def create_task(task_create: TaskCreateRequest, task_service: TaskService = Depends(TaskService), current_user: User = Depends(get_current_user)):
    
    # Save task
    new_task = task_service.create_task(task_create, current_user.user_id)

    return SuccessResponse(result=new_task)


@task_router.get("/detail/{task_id}")
async def get_user(task_id: str, task_service: TaskService = Depends(TaskService), current_user: User = Depends(get_current_user)):
    
    task = task_service.get_task_by_id(task_id, current_user.user_id)

    return SuccessResponse(result=task)

@task_router.get("/tasks-by-room")
async def get_user(room_id: str, task_service: TaskService = Depends(TaskService), current_user: User = Depends(get_current_user)):
    
    list_tasks = task_service.get_list_task_by_room_id(room_id, current_user.user_id)

    return SuccessResponse(result=list_tasks)

@task_router.put("/update-status")
async def get_user(task_id: str, status: str, task_service: TaskService = Depends(TaskService), current_user: User = Depends(get_current_user)):
    
    task = task_service.update_task_status(task_id, status, current_user.user_id)

    return SuccessResponse(result=task)

@task_router.delete("/{task_id}")
async def get_user(task_id: str, task_service: TaskService = Depends(TaskService), current_user: User = Depends(get_current_user)):

    return task_service.delete_task_by_id(task_id, current_user.user_id)