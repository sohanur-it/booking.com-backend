# Booking.com Clone Backend API

A comprehensive FastAPI backend that replicates all core Booking.com functionality, designed to work completely offline with mock data.

## 🚀 Features

### Authentication & User Management

- **User Registration & Login**: Secure JWT-based authentication
- **Password Reset**: Complete password reset flow
- **User Profiles**: Manage user information and preferences
- **Genius Loyalty Program**: Automatic level progression and discount calculation

### Genius Loyalty Program

- **Level Progression**: Automatic advancement based on bookings and spending
- **Discount Calculation**: 10%, 15%, 20% discounts for Levels 1, 2, 3
- **Progress Tracking**: Real-time tracking of next level requirements
- **Spending Analytics**: Total bookings and amount spent tracking

### Property Management

- **Property CRUD**: Complete property lifecycle management
- **Room Management**: Room types, availability, and pricing
- **Amenities & Facilities**: Comprehensive feature tracking
- **Search & Discovery**: Advanced filtering and search capabilities

### Booking System

- **Complete Booking Flow**: From search to confirmation
- **Price Calculation**: Real-time pricing with Genius discounts
- **Availability Management**: Smart availability checking
- **Payment Integration**: Payment method management
- **Cancellation Logic**: Flexible cancellation policies

### Review System

- **Post-Stay Reviews**: Only completed stays can be reviewed
- **Multi-Category Ratings**: Cleanliness, comfort, location, etc.
- **Review Moderation**: Approval and filtering system
- **Helpful Voting**: Community-driven review quality
- **Owner Responses**: Property owner response system

### Search & Discovery

- **Advanced Search**: Destination, dates, guests, filters
- **Price Filtering**: Min/max price ranges
- **Rating Filters**: Star ratings and review scores
- **Amenity Filters**: Property and room amenities
- **Sorting Options**: Price, rating, distance, recommendations

## 🛠️ Technology Stack

- **Framework**: FastAPI
- **Database**: SQLite (for offline capability)
- **ORM**: SQLAlchemy
- **Authentication**: JWT with Python-Jose
- **Password Hashing**: Passlib with bcrypt
- **Validation**: Pydantic
- **Documentation**: Auto-generated OpenAPI/Swagger

## 📋 Prerequisites

- Python 3.9+
- UV package manager (recommended) or pip

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd apps/backend
uv sync
```

### 2. Run the Server

```bash
# Using UV (recommended)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the NX command
npx nx serve backend
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Documentation

### Authentication Endpoints

#### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Get Genius Info

```http
GET /api/v1/auth/genius-info
Authorization: Bearer <jwt-token>
```

### Property Search

#### Search Properties

```http
GET /api/v1/properties/search?destination=New%20York&check_in=2024-01-15&check_out=2024-01-20&guests=2&min_price=100&max_price=500&star_rating=4,5
```

#### Get Property Details

```http
GET /api/v1/properties/1
```

### Booking Management

#### Calculate Price

```http
POST /api/v1/bookings/calculate-price
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "room_id": 1,
  "check_in_date": "2024-01-15T00:00:00",
  "check_out_date": "2024-01-20T00:00:00",
  "num_guests": 2,
  "num_rooms": 1
}
```

#### Create Booking

```http
POST /api/v1/bookings/
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "room_id": 1,
  "check_in_date": "2024-01-15T00:00:00",
  "check_out_date": "2024-01-20T00:00:00",
  "num_guests": 2,
  "guest_names": ["John Doe", "Jane Doe"],
  "special_requests": "Early check-in if possible"
}
```

### Review System

#### Submit Review

```http
POST /api/v1/reviews/
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "property_id": 1,
  "booking_id": 1,
  "title": "Excellent stay!",
  "content": "Great location, clean rooms, friendly staff.",
  "overall_rating": 9.0,
  "cleanliness_rating": 9.5,
  "comfort_rating": 8.5,
  "location_rating": 9.0,
  "facilities_rating": 8.0,
  "staff_rating": 9.5,
  "value_for_money_rating": 8.5
}
```

## 🗄️ Database Schema

### Users Table

- User authentication and profile data
- Genius loyalty program tracking
- Booking count and spending totals

### Properties Table

- Property information and details
- Amenities and facilities (JSON)
- Location and contact information

### Rooms Table

- Room types and configurations
- Pricing (base and Genius prices)
- Availability tracking

### Bookings Table

- Complete booking records
- Status tracking (pending, confirmed, cancelled)
- Payment information

### Reviews Table

- User reviews and ratings
- Multi-category rating system
- Moderation and helpful voting

### Payment Methods Table

- User payment method storage
- Credit card information (encrypted)
- Default payment method tracking

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for secure password storage
- **Input Validation**: Comprehensive Pydantic validation
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **CORS Configuration**: Proper cross-origin resource sharing

## 🎯 Genius Loyalty Program

### Level Requirements

- **Level 1**: 1+ bookings → 10% discount
- **Level 2**: 5+ bookings, $1000+ spent → 15% discount
- **Level 3**: 15+ bookings, $5000+ spent → 20% discount

### Automatic Features

- Real-time level calculation
- Automatic discount application
- Progress tracking for next level
- Spending analytics

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src
```

## 📦 Development

### Project Structure

```
src/
├── api/
│   ├── __init__.py          # Main API configuration
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database configuration
│   ├── auth.py              # Authentication utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── booking.py
│   │   └── review.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── booking.py
│   │   └── review.py
│   └── routers/             # API route handlers
│       ├── auth.py
│       ├── properties.py
│       ├── bookings.py
│       └── reviews.py
```

### Adding New Features

1. **Create Model**: Add SQLAlchemy model in `models/`
2. **Create Schema**: Add Pydantic schemas in `schemas/`
3. **Create Router**: Add API endpoints in `routers/`
4. **Update Main**: Include router in `__init__.py`

## 🌐 Offline Capability

This API is designed to work completely offline:

- SQLite database for local storage
- Mock data generation capabilities
- No external API dependencies
- Perfect for development and demonstrations

## 📄 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues, please check the API documentation at `/docs` or create an issue in the repository.
