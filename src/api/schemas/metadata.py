from pydantic import BaseModel
from typing import Optional


class FacilityCodeCreate(BaseModel):
    code: str
    label: str
    scope: str  # property, room


class FacilityCodeResponse(BaseModel):
    id: int
    code: str
    label: str
    scope: str

    class Config:
        from_attributes = True


