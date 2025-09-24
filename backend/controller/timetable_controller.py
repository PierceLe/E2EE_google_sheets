from service.timetable_event_service import TimetableEventService
from dto.request.timetable.create_event_request import CreateEventRequest
from dto.request.timetable.update_event_request import UpdateEventRequest
from dto.request.timetable.get_events_by_range_request import GetEventsByRangeRequest
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from dto.response.success_response import SuccessResponse
from utils.utils import get_current_user
from model.user import User
from typing import Optional

from service.friend_service import FriendService

timetable_router = APIRouter()

@timetable_router.post("/create")
async def create_event(
    event_request: CreateEventRequest, 
    timetable_service: TimetableEventService = Depends(TimetableEventService), 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new timetable event for the current user
    """
    new_event = timetable_service.create_event(event_request, current_user.user_id)
    return SuccessResponse(result=new_event)

@timetable_router.get("/detail/{event_id}")
async def get_event(
    event_id: str, 
    timetable_service: TimetableEventService = Depends(TimetableEventService), 
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific event by ID
    """
    event = timetable_service.get_event_by_id(event_id, current_user.user_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return SuccessResponse(result=event)

@timetable_router.get("/all")
async def get_all_events(
    timetable_service: TimetableEventService = Depends(TimetableEventService), 
    current_user: User = Depends(get_current_user)
):
    """
    Get all events for the current user
    """
    events = timetable_service.get_all_events(current_user.user_id)
    return SuccessResponse(result=events)

@timetable_router.post("/by-date-range")
async def get_events_by_range(
    range_request: GetEventsByRangeRequest,
    timetable_service: TimetableEventService = Depends(TimetableEventService), 
    current_user: User = Depends(get_current_user)
):
    """
    Get events for the current user within a specified date range
    """
    events = timetable_service.get_events_by_date_range(
        range_request.start_date, 
        range_request.end_date, 
        current_user.user_id
    )
    return SuccessResponse(result=events)

@timetable_router.put("/update")
async def update_event(
    update_request: UpdateEventRequest, 
    timetable_service: TimetableEventService = Depends(TimetableEventService), 
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing event
    """
    updated_event = timetable_service.update_event(update_request, current_user.user_id)
    
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return SuccessResponse(result=updated_event)

@timetable_router.delete("/{event_id}")
async def delete_event(
    event_id: str, 
    timetable_service: TimetableEventService = Depends(TimetableEventService), 
    current_user: User = Depends(get_current_user)
):
    """
    Delete an event by ID
    """
    result = timetable_service.delete_event(event_id, current_user.user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return SuccessResponse(result=True)


@timetable_router.get("/friend/{friend_id}")
async def get_friend_timetable(
        friend_id: str,
        timetable_service: TimetableEventService = Depends(TimetableEventService),
        friend_service: FriendService = Depends(FriendService),
        current_user: User = Depends(get_current_user)
):
    """
    Get all events for a specific friend
    """
    # Verify friendship
    if not friend_service.is_friend(current_user.user_id, friend_id):
        raise HTTPException(status_code=403, detail="Not authorized to view this friend's timetable.")

    events = timetable_service.get_all_events(friend_id)
    return SuccessResponse(result=events)