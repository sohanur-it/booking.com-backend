from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get("/")
def list_activities(city: Optional[str] = Query(None)):
    sample = [
        {"id": 1, "name": "City Walking Tour", "city": city or "New York", "duration": "3h"},
        {"id": 2, "name": "Museum Pass", "city": city or "New York", "duration": "Day"},
    ]
    return sample


@router.post("/{activity_id}/book")
def book_activity(activity_id: int):
    return {"message": f"Booked activity {activity_id}"}


