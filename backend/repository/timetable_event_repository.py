from sqlalchemy.orm import Session
from database import SessionLocal
from model.timetable_event import TimetableEvent
from typing import List, Optional
import datetime

class TimetableEventRepository:
    def create_event(
        self,
        user_id: str,
        title: str,
        description: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        location: str = None,
        color: str = None,
        is_recurring: bool = False,
        recurrence_pattern: str = None
    ) -> TimetableEvent:
        with SessionLocal() as db:
            db_event = TimetableEvent(
                user_id=user_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location,
                color=color,
                is_recurring=is_recurring,
                recurrence_pattern=recurrence_pattern
            )
            db.add(db_event)
            db.commit()
            db.refresh(db_event)
            return db_event

    def get_event_by_id(self, event_id: str) -> Optional[TimetableEvent]:
        with SessionLocal() as db:
            return db.query(TimetableEvent).filter(TimetableEvent.event_id == event_id).first()

    def get_events_by_user_id(self, user_id: str) -> List[TimetableEvent]:
        with SessionLocal() as db:
            return (
                db.query(TimetableEvent)
                .filter(TimetableEvent.user_id == user_id)
                .order_by(TimetableEvent.start_time)
                .all()
            )
    
    def get_events_by_date_range(self, user_id: str, start_date: datetime.datetime, end_date: datetime.datetime) -> List[TimetableEvent]:
        with SessionLocal() as db:
            return (
                db.query(TimetableEvent)
                .filter(TimetableEvent.user_id == user_id)
                .filter(TimetableEvent.start_time >= start_date)
                .filter(TimetableEvent.start_time <= end_date)
                .order_by(TimetableEvent.start_time)
                .all()
            )

    def update_event(
        self,
        event_id: str,
        title: str = None,
        description: str = None,
        start_time: datetime.datetime = None,
        end_time: datetime.datetime = None,
        location: str = None,
        color: str = None,
        is_recurring: bool = None,
        recurrence_pattern: str = None
    ) -> Optional[TimetableEvent]:
        with SessionLocal() as db:
            db_event = db.query(TimetableEvent).filter(TimetableEvent.event_id == event_id).first()
            if db_event:
                if title is not None:
                    db_event.title = title
                if description is not None:
                    db_event.description = description
                if start_time is not None:
                    db_event.start_time = start_time
                if end_time is not None:
                    db_event.end_time = end_time
                if location is not None:
                    db_event.location = location
                if color is not None:
                    db_event.color = color
                if is_recurring is not None:
                    db_event.is_recurring = is_recurring
                if recurrence_pattern is not None:
                    db_event.recurrence_pattern = recurrence_pattern
                
                db.commit()
                db.refresh(db_event)
                return db_event
            return None

    def delete_event(self, event_id: str) -> bool:
        with SessionLocal() as db:
            db_event = db.query(TimetableEvent).filter(TimetableEvent.event_id == event_id).first()
            if db_event:
                db.delete(db_event)
                db.commit()
                return True
            return False 