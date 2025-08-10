from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.metadata import FacilityCode
from ..schemas.metadata import FacilityCodeCreate, FacilityCodeResponse
from ..auth import get_current_active_user

router = APIRouter(prefix="/metadata", tags=["Property Metadata"])


@router.get("/facilities", response_model=List[FacilityCodeResponse])
def list_facilities(scope: str | None = None, db: Session = Depends(get_db)):
    q = db.query(FacilityCode)
    if scope:
        q = q.filter(FacilityCode.scope == scope)
    return [FacilityCodeResponse.from_orm(f) for f in q.all()]


@router.post("/facilities", response_model=FacilityCodeResponse)
def create_facility(
    body: FacilityCodeCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    if db.query(FacilityCode).filter(FacilityCode.code == body.code).first():
        raise HTTPException(status_code=400, detail="Facility code already exists")
    f = FacilityCode(code=body.code, label=body.label, scope=body.scope)
    db.add(f)
    db.commit()
    db.refresh(f)
    return FacilityCodeResponse.from_orm(f)


@router.delete("/facilities/{facility_id}")
def delete_facility(facility_id: int, db: Session = Depends(get_db), _user=Depends(get_current_active_user)):
    f = db.query(FacilityCode).filter(FacilityCode.id == facility_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(f)
    db.commit()
    return {"message": "Deleted"}


