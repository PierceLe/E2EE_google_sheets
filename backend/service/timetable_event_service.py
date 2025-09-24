from repository.timetable_event_repository import TimetableEventRepository
from dto.response.timetable.event_response import EventResponse
from dto.request.timetable.create_event_request import CreateEventRequest
from dto.request.timetable.update_event_request import UpdateEventRequest
from typing import List, Optional
from exception.app_exception import AppException
from exception.error_code import ErrorCode
import datetime

class TimetableEventService:
    def __init__(self):
        self.timetable_repository = TimetableEventRepository()

    def create_event(self, event_request: CreateEventRequest, current_user_id: str) -> EventResponse:
        # Validate start time is before end time
        if event_request.start_time >= event_request.end_time:
            raise AppException(ErrorCode.INVALID_TIME_RANGE)

        event = self.timetable_repository.create_event(
            user_id=current_user_id,
            title=event_request.title,
            description=event_request.description,
            start_time=event_request.start_time,
            end_time=event_request.end_time,
            location=event_request.location,
            color=event_request.color,
            is_recurring=event_request.is_recurring,
            recurrence_pattern=event_request.recurrence_pattern
        )

        return self._map_to_response(event)
    
    def get_event_by_id(self, event_id: str, current_user_id: str) -> Optional[EventResponse]:
        event = self.timetable_repository.get_event_by_id(event_id=event_id)

        if not event:
            return None
        
        # Check if the event belongs to the current user
        if event.user_id != current_user_id:
            raise AppException(ErrorCode.NOT_PERMISSION)

        return self._map_to_response(event)
    
    def get_all_events(self, current_user_id: str) -> List[EventResponse]:
        events = self.timetable_repository.get_events_by_user_id(current_user_id)
        
        if not events:
            return []
        
        return [self._map_to_response(event) for event in events]
    
    def get_events_by_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime, current_user_id: str) -> List[EventResponse]:
        if start_date > end_date:
            raise AppException(ErrorCode.INVALID_TIME_RANGE)
            
        events = self.timetable_repository.get_events_by_date_range(current_user_id, start_date, end_date)
        
        if not events:
            return []
        
        return [self._map_to_response(event) for event in events]
    
    def update_event(self, update_request: UpdateEventRequest, current_user_id: str) -> Optional[EventResponse]:
        event = self.timetable_repository.get_event_by_id(event_id=update_request.event_id)
        
        if not event:
            return None
        
        # Check if the event belongs to the current user
        if event.user_id != current_user_id:
            raise AppException(ErrorCode.NOT_PERMISSION)
        
        # Validate times if both are provided
        if update_request.start_time and update_request.end_time and update_request.start_time >= update_request.end_time:
            raise AppException(ErrorCode.INVALID_TIME_RANGE)
        
        # If only one time is provided, validate against existing value
        if update_request.start_time and not update_request.end_time and update_request.start_time >= event.end_time:
            raise AppException(ErrorCode.INVALID_TIME_RANGE)
        
        if update_request.end_time and not update_request.start_time and event.start_time >= update_request.end_time:
            raise AppException(ErrorCode.INVALID_TIME_RANGE)

        updated_event = self.timetable_repository.update_event(
            event_id=update_request.event_id,
            title=update_request.title,
            description=update_request.description,
            start_time=update_request.start_time,
            end_time=update_request.end_time,
            location=update_request.location,
            color=update_request.color,
            is_recurring=update_request.is_recurring,
            recurrence_pattern=update_request.recurrence_pattern
        )

        return self._map_to_response(updated_event)
    
    def delete_event(self, event_id: str, current_user_id: str) -> bool:
        event = self.timetable_repository.get_event_by_id(event_id=event_id)
        
        if not event:
            return False
        
        # Check if the event belongs to the current user
        if event.user_id != current_user_id:
            raise AppException(ErrorCode.NOT_PERMISSION)

        return self.timetable_repository.delete_event(event_id)
    
    def _map_to_response(self, event) -> EventResponse:
        return EventResponse(
            event_id=event.event_id,
            user_id=event.user_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            color=event.color,
            is_recurring=event.is_recurring,
            recurrence_pattern=event.recurrence_pattern,
            created_at=event.created_at,
            updated_at=event.updated_at
        ) 