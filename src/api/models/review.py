from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    
    # Review content
    title = Column(String(255))
    content = Column(Text, nullable=False)
    
    # Ratings (1-10 scale like Booking.com)
    overall_rating = Column(Float, nullable=False)
    cleanliness_rating = Column(Float)
    comfort_rating = Column(Float)
    location_rating = Column(Float)
    facilities_rating = Column(Float)
    staff_rating = Column(Float)
    value_for_money_rating = Column(Float)
    wifi_rating = Column(Float)
    
    # Review metadata
    is_verified_stay = Column(Boolean, default=True)  # Only post-stay reviews
    helpful_votes = Column(Integer, default=0)
    is_helpful = Column(Boolean, default=False)
    
    # Moderation
    is_approved = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)
    moderation_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    property = relationship("Property", back_populates="reviews")
    booking = relationship("Booking")
    
    def __repr__(self):
        return f"<Review(id={self.id}, rating={self.overall_rating}, property_id={self.property_id})>"

class ReviewResponse(Base):
    __tablename__ = "review_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    
    # Response content
    content = Column(Text, nullable=False)
    responder_type = Column(String(50))  # property_owner, manager, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    review = relationship("Review")
    
    def __repr__(self):
        return f"<ReviewResponse(id={self.id}, review_id={self.review_id})>" 