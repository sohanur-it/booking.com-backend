from sqlalchemy import Column, Integer, String
from ..database import Base


class FacilityCode(Base):
    __tablename__ = "facility_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    label = Column(String(255), nullable=False)
    scope = Column(String(32), nullable=False)  # property, room

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FacilityCode(code='{self.code}', scope='{self.scope}')>"


