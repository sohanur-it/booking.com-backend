from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.review import Review, ReviewResponse as ReviewResponseModel
from ..models.booking import Booking, BookingStatus
from ..models.property import Property
from ..models.user import User
from ..schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithProperty,
    ReviewSearch, ReviewSearchResponse, ReviewHelpfulVote,
    ReviewResponseCreate, ReviewResponseResponse
)
from ..auth import get_current_active_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=ReviewResponse)
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new review for a property."""
    
    # Verify the booking exists and belongs to the user
    booking = db.query(Booking).filter(
        and_(
            Booking.id == review_data.booking_id,
            Booking.user_id == current_user.id,
            Booking.property_id == review_data.property_id
        )
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to you"
        )
    
    # Check if user has already reviewed this booking
    existing_review = db.query(Review).filter(
        and_(
            Review.booking_id == review_data.booking_id,
            Review.user_id == current_user.id
        )
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this booking"
        )
    
    # Verify the booking is completed (check-out date has passed)
    if booking.check_out_date > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only review completed stays"
        )
    
    # Create review
    db_review = Review(
        user_id=current_user.id,
        property_id=review_data.property_id,
        booking_id=review_data.booking_id,
        title=review_data.title,
        content=review_data.content,
        overall_rating=review_data.overall_rating,
        cleanliness_rating=review_data.cleanliness_rating,
        comfort_rating=review_data.comfort_rating,
        location_rating=review_data.location_rating,
        facilities_rating=review_data.facilities_rating,
        staff_rating=review_data.staff_rating,
        value_for_money_rating=review_data.value_for_money_rating,
        wifi_rating=review_data.wifi_rating,
        is_verified_stay=True
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Add user info for response
    review_dict = ReviewResponse.from_orm(db_review).dict()
    review_dict.update({
        "user_first_name": current_user.first_name,
        "user_last_name": current_user.last_name
    })
    
    return ReviewResponse(**review_dict)

@router.get("/", response_model=ReviewSearchResponse)
def search_reviews(
    property_id: Optional[int] = Query(None, description="Filter by property ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    min_rating: Optional[float] = Query(None, ge=1, le=10, description="Minimum rating"),
    max_rating: Optional[float] = Query(None, ge=1, le=10, description="Maximum rating"),
    rating_type: Optional[str] = Query(None, description="Rating type to filter by"),
    is_verified_stay: Optional[bool] = Query(None, description="Filter by verified stays only"),
    sort_by: str = Query("created_at", description="Sort by: created_at, rating, helpful_votes"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Search and filter reviews."""
    
    # Build base query
    query = db.query(Review).filter(Review.is_approved == True)
    
    # Apply filters
    if property_id:
        query = query.filter(Review.property_id == property_id)
    
    if user_id:
        query = query.filter(Review.user_id == user_id)
    
    if min_rating is not None:
        if rating_type and rating_type != "overall":
            # Filter by specific rating type
            rating_column = getattr(Review, f"{rating_type}_rating")
            query = query.filter(rating_column >= min_rating)
        else:
            query = query.filter(Review.overall_rating >= min_rating)
    
    if max_rating is not None:
        if rating_type and rating_type != "overall":
            rating_column = getattr(Review, f"{rating_type}_rating")
            query = query.filter(rating_column <= max_rating)
        else:
            query = query.filter(Review.overall_rating <= max_rating)
    
    if is_verified_stay is not None:
        query = query.filter(Review.is_verified_stay == is_verified_stay)
    
    # Apply sorting
    if sort_by == "rating":
        sort_column = Review.overall_rating
    elif sort_by == "helpful_votes":
        sort_column = Review.helpful_votes
    else:  # created_at
        sort_column = Review.created_at
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count
    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit
    offset = (page - 1) * limit
    
    # Get paginated results
    reviews = query.offset(offset).limit(limit).all()
    
    # Calculate average rating and distribution
    avg_rating = db.query(func.avg(Review.overall_rating)).filter(
        Review.is_approved == True
    ).scalar() or 0.0
    
    # Rating distribution (1-10 scale)
    rating_distribution = {}
    for i in range(1, 11):
        count = db.query(Review).filter(
            and_(Review.overall_rating == i, Review.is_approved == True)
        ).count()
        rating_distribution[str(i)] = count
    
    # Build response with property info
    review_responses = []
    for review in reviews:
        # Get user info
        user = db.query(User).filter(User.id == review.user_id).first()
        # Get property info
        property = db.query(Property).filter(Property.id == review.property_id).first()
        
        review_dict = ReviewResponse.from_orm(review).dict()
        review_dict.update({
            "user_first_name": user.first_name if user else "",
            "user_last_name": user.last_name if user else "",
            "property_name": property.name if property else "",
            "property_city": property.city if property else "",
            "property_country": property.country if property else ""
        })
        
        review_responses.append(ReviewWithProperty(**review_dict))
    
    return ReviewSearchResponse(
        reviews=review_responses,
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        average_rating=float(avg_rating),
        rating_distribution=rating_distribution
    )

@router.get("/{review_id}", response_model=ReviewWithProperty)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review."""
    review = db.query(Review).filter(
        and_(Review.id == review_id, Review.is_approved == True)
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Get user and property info
    user = db.query(User).filter(User.id == review.user_id).first()
    property = db.query(Property).filter(Property.id == review.property_id).first()
    
    review_dict = ReviewResponse.from_orm(review).dict()
    review_dict.update({
        "user_first_name": user.first_name if user else "",
        "user_last_name": user.last_name if user else "",
        "property_name": property.name if property else "",
        "property_city": property.city if property else "",
        "property_country": property.country if property else ""
    })
    
    return ReviewWithProperty(**review_dict)

@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a review (only by the author)."""
    review = db.query(Review).filter(
        and_(
            Review.id == review_id,
            Review.user_id == current_user.id
        )
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or you don't have permission to edit it"
        )
    
    # Update fields
    for field, value in review_update.dict(exclude_unset=True).items():
        setattr(review, field, value)
    
    db.commit()
    db.refresh(review)
    
    # Add user info for response
    review_dict = ReviewResponse.from_orm(review).dict()
    review_dict.update({
        "user_first_name": current_user.first_name,
        "user_last_name": current_user.last_name
    })
    
    return ReviewResponse(**review_dict)

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a review (only by the author)."""
    review = db.query(Review).filter(
        and_(
            Review.id == review_id,
            Review.user_id == current_user.id
        )
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or you don't have permission to delete it"
        )
    
    db.delete(review)
    db.commit()
    
    return {"message": "Review deleted successfully"}

@router.post("/{review_id}/helpful")
def mark_review_helpful(
    review_id: int,
    vote: ReviewHelpfulVote,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark a review as helpful or not helpful."""
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Update helpful votes
    if vote.is_helpful:
        review.helpful_votes += 1
    else:
        review.helpful_votes = max(0, review.helpful_votes - 1)
    
    db.commit()
    
    return {"message": "Vote recorded successfully", "helpful_votes": review.helpful_votes}

# Property owner responses to reviews
@router.post("/{review_id}/response", response_model=ReviewResponseResponse)
def create_review_response(
    review_id: int,
    response_data: ReviewResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a response to a review (property owner only)."""
    # Verify review exists
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if response already exists
    existing_response = db.query(ReviewResponseModel).filter(
        ReviewResponseModel.review_id == review_id
    ).first()
    
    if existing_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Response already exists for this review"
        )
    
    # Create response
    db_response = ReviewResponseModel(
        review_id=review_id,
        content=response_data.content,
        responder_type=response_data.responder_type
    )
    
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return ReviewResponseResponse.from_orm(db_response)

@router.get("/{review_id}/response", response_model=ReviewResponseResponse)
def get_review_response(review_id: int, db: Session = Depends(get_db)):
    """Get the response to a review."""
    response = db.query(ReviewResponseModel).filter(
        ReviewResponseModel.review_id == review_id
    ).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No response found for this review"
        )
    
    return ReviewResponseResponse.from_orm(response) 