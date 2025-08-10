from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.get("/search")
def search_packages(
    destination: str = Query(...),
    check_in: Optional[str] = Query(None),
    check_out: Optional[str] = Query(None),
    include_flight: bool = Query(True),
    include_car: bool = Query(False),
):
    # Minimal scaffold response; pricing/combination happens in frontend for now
    return {
        "destination": destination,
        "check_in": check_in,
        "check_out": check_out,
        "include_flight": include_flight,
        "include_car": include_car,
        "message": "Packages search scaffolding in place",
    }


