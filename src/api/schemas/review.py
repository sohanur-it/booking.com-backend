from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# Review Create
class ReviewCreate(BaseModel):
    property_id: int
    booking_id: int
    title: Optional[str] = None
    content: str
    overall_rating: float
    cleanliness_rating: Optional[float] = None
    comfort_rating: Optional[float] = None
    location_rating: Optional[float] = None
    facilities_rating: Optional[float] = None
    staff_rating: Optional[float] = None
    value_for_money_rating: Optional[float] = None
    wifi_rating: Optional[float] = None
    
    @field_validator('overall_rating')
    def validate_overall_rating(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Overall rating must be between 1 and 10')
        return v
    
    @field_validator('cleanliness_rating', 'comfort_rating', 'location_rating', 
               'facilities_rating', 'staff_rating', 'value_for_money_rating', 'wifi_rating')
    def validate_ratings(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Rating must be between 1 and 10')
        return v
    
    @field_validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Review content must be at least 10 characters long')
        return v

# Review Update
class ReviewUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    overall_rating: Optional[float] = None
    cleanliness_rating: Optional[float] = None
    comfort_rating: Optional[float] = None
    location_rating: Optional[float] = None
    facilities_rating: Optional[float] = None
    staff_rating: Optional[float] = None
    value_for_money_rating: Optional[float] = None
    wifi_rating: Optional[float] = None
    
    @field_validator('overall_rating')
    def validate_overall_rating(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Overall rating must be between 1 and 10')
        return v
    
    @field_validator('cleanliness_rating', 'comfort_rating', 'location_rating', 
               'facilities_rating', 'staff_rating', 'value_for_money_rating', 'wifi_rating')
    def validate_ratings(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Rating must be between 1 and 10')
        return v
    
    @field_validator('content')
    def validate_content(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError('Review content must be at least 10 characters long')
        return v

# Review Response (single authoritative definition)
class ReviewResponse(BaseModel):
    id: int
    user_id: int
    property_id: int
    booking_id: int
    title: Optional[str]
    content: str
    overall_rating: float
    cleanliness_rating: Optional[float]
    comfort_rating: Optional[float]
    location_rating: Optional[float]
    facilities_rating: Optional[float]
    staff_rating: Optional[float]
    value_for_money_rating: Optional[float]
    wifi_rating: Optional[float]
    is_verified_stay: bool
    helpful_votes: int
    is_helpful: bool
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    
    # User info (for display)
    user_first_name: str = ""
    user_last_name: str = ""
    
    class Config:
        from_attributes = True

# Review Search/Filter
class ReviewSearch(BaseModel):
    property_id: Optional[int] = None
    user_id: Optional[int] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    rating_type: Optional[str] = None  # overall, cleanliness, etc.
    is_verified_stay: Optional[bool] = None
    sort_by: Optional[str] = "created_at"  # created_at, rating, helpful_votes
    sort_order: Optional[str] = "desc"  # asc, desc
    page: Optional[int] = 1
    limit: Optional[int] = 20
    
    @field_validator('min_rating', 'max_rating')
    def validate_rating_range(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Rating must be between 1 and 10')
        return v

 

# Review with Property Info
class ReviewWithProperty(ReviewResponse):
    property_name: str
    property_city: str
    property_country: str

 

# Review Search Response
class ReviewSearchResponse(BaseModel):
    reviews: List[ReviewWithProperty]
    total_count: int
    page: int
    limit: int
    total_pages: int
    average_rating: float
    rating_distribution: dict  # Distribution of ratings (1-10)

 

# Review Helpful Vote
class ReviewHelpfulVote(BaseModel):
    review_id: int
    is_helpful: bool

# Review Response Create
class ReviewResponseCreate(BaseModel):
    review_id: int
    content: str
    responder_type: str = "property_owner"
    
    @field_validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Response content must be at least 5 characters long')
        return v

# Review Response Response
class ReviewResponseResponse(BaseModel):
    id: int
    review_id: int
    content: str
    responder_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 