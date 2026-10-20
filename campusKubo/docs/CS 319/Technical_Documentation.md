# Technical Documentation

## System Architecture Diagram

```plantuml
@startuml System Architecture
!theme plain
skinparam backgroundColor #FEFEFE
skinparam componentStyle uml2

title campusKubo System Architecture

package "Client Layer" as CL {
    [Web Browser] as Browser
    [Flet Web App] as FletApp
}

package "Application Layer" as AL {
    [Flet Server] as FletServer
    [Auth Service] as AuthService
    [User Service] as UserService
    [Listing Service] as ListingService
    [Reservation Service] as ReservationService
    [Notification Service] as NotificationService
    [Admin Service] as AdminService
    [Activity Service] as ActivityService
    [Report Service] as ReportService
    [Settings Service] as SettingsService
    [GMaps Service] as GMapsService
}

package "Data Layer" as DL {
    [SQLite Database] as DB
    database "users" as Users
    database "listings" as Listings
    database "listing_images" as Images
    database "reservations" as Reservations
    database "payments" as Payments
    database "notifications" as Notifications
    database "activity_logs" as ActivityLogs
    database "reports" as Reports
    database "user_addresses" as Addresses
    database "saved_listings" as Saved
    database "tenants" as Tenants
    database "user_settings" as UserSettings
    database "reviews" as Reviews
    database "messages" as Messages
    database "system_settings" as SystemSettings
}

package "External Services" as ES {
    [Google Maps API] as Maps
    [Email Service] as Email
    [File Storage] as Files
}

Browser --> FletApp : HTTP/WebSocket
FletApp --> FletServer : Flet Protocol

FletServer --> AuthService : Authentication
FletServer --> UserService : User Management
FletServer --> ListingService : Property Management
FletServer --> ReservationService : Booking Management
FletServer --> NotificationService : Notifications
FletServer --> AdminService : Administration
FletServer --> ActivityService : Activity Logging
FletServer --> ReportService : Report Management
FletServer --> SettingsService : System Settings
FletServer --> GMapsService : Geocoding

AuthService --> DB
UserService --> DB
ListingService --> DB
ReservationService --> DB
NotificationService --> DB
AdminService --> DB
ActivityService --> DB
ReportService --> DB
SettingsService --> DB

DB --> Users
DB --> Listings
DB --> Images
DB --> Reservations
DB --> Payments
DB --> Notifications
DB --> ActivityLogs
DB --> Reports
DB --> Addresses
DB --> Saved
DB --> Tenants
DB --> UserSettings
DB --> Reviews
DB --> Messages
DB --> SystemSettings

ListingSvc --> Maps : Geocoding
NotifSvc --> Email : Send Emails
UserSvc --> Files : Avatar Storage
ListingSvc --> Files : Image Storage
@enduml
```

## Database Schema ERD

```plantuml
@startuml Database Schema ERD
!theme plain
skinparam backgroundColor #FEFEFE

title campusKubo Database Schema

entity "users" as users {
    + id : INTEGER <<PK>>
    + email : TEXT <<UQ>>
    + password : TEXT
    + role : TEXT
    + full_name : TEXT
    + phone : TEXT
    + is_verified : BOOLEAN
    + is_active : BOOLEAN
    + created_at : DATETIME
    + deleted_at : DATETIME
}

entity "listings" as listings {
    + id : INTEGER <<PK>>
    + pm_id : INTEGER <<FK>>
    + address : TEXT
    + price : REAL
    + description : TEXT
    + lodging_details : TEXT
    + status : TEXT
    + images : TEXT
    + created_at : DATETIME
    + updated_at : DATETIME
}

entity "listing_images" as listing_images {
    + id : INTEGER <<PK>>
    + listing_id : INTEGER <<FK>>
    + image_path : TEXT
}

entity "reservations" as reservations {
    + id : INTEGER <<PK>>
    + listing_id : INTEGER <<FK>>
    + tenant_id : INTEGER <<FK>>
    + start_date : TEXT
    + end_date : TEXT
    + status : TEXT
    + created_at : DATETIME
}

entity "payments" as payments {
    + id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + listing_id : INTEGER <<FK>>
    + amount : REAL
    + status : TEXT
    + payment_method : TEXT
    + refunded_amount : REAL
    + created_at : DATETIME
    + updated_at : DATETIME
}

entity "notifications" as notifications {
    + notification_id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + notification_type : TEXT
    + category : TEXT
    + message : TEXT
    + is_read : BOOLEAN
    + reference_id : INTEGER
    + created_at : DATETIME
}

entity "activity_logs" as activity_logs {
    + id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + action : TEXT
    + details : TEXT
    + created_at : DATETIME
}

entity "reports" as reports {
    + id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + listing_id : INTEGER <<FK>>
    + message : TEXT
    + status : TEXT
    + assigned_admin_id : INTEGER
    + assigned_at : DATETIME
    + assigned_note : TEXT
    + created_at : DATETIME
}

entity "user_addresses" as user_addresses {
    + address_id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + house_no : TEXT
    + street : TEXT
    + barangay : TEXT
    + city : TEXT
    + province : TEXT
    + postal_code : TEXT
    + is_primary : BOOLEAN
}

entity "saved_listings" as saved_listings {
    + saved_id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + listing_id : INTEGER <<FK>>
    + saved_at : DATETIME
}

entity "tenants" as tenants {
    + id : INTEGER <<PK>>
    + owner_id : INTEGER <<FK>>
    + name : TEXT
    + room_number : TEXT
    + room_type : TEXT
    + status : TEXT
    + avatar : TEXT
    + created_at : DATETIME
}

entity "user_settings" as user_settings {
    + setting_id : INTEGER <<PK>>
    + user_id : INTEGER <<FK>>
    + popup_notifications : BOOLEAN
    + chat_notifications : BOOLEAN
    + email_notifications : BOOLEAN
    + theme : TEXT
    + language : TEXT
    + created_at : DATETIME
}

entity "reviews" as reviews {
    + review_id : INTEGER <<PK>>
    + listing_id : INTEGER <<FK>>
    + user_id : INTEGER <<FK>>
    + rating : INTEGER
    + comment : TEXT
    + created_at : DATETIME
}

entity "messages" as messages {
    + message_id : INTEGER <<PK>>
    + sender_id : INTEGER <<FK>>
    + receiver_id : INTEGER <<FK>>
    + content : TEXT
    + is_read : BOOLEAN
    + created_at : DATETIME
}

entity "system_settings" as system_settings {
    + id : INTEGER <<PK>>
    + settings_id : TEXT <<UQ>>
    + settings_json : TEXT
    + created_at : DATETIME
    + updated_at : DATETIME
}

users ||--o{ listings : owns
users ||--o{ reservations : makes
users ||--o{ payments : pays
users ||--o{ notifications : receives
users ||--o{ activity_logs : generates
users ||--o{ reports : creates
users ||--o{ user_addresses : has
users ||--o{ saved_listings : saves
users ||--o{ tenants : manages
users ||--o{ user_settings : configures
users ||--o{ reviews : writes
users ||--o{ messages : sends

listings ||--o{ listing_images : has
listings ||--o{ reservations : booked_for
listings ||--o{ payments : receives
listings ||--o{ saved_listings : saved_by
listings ||--o{ reviews : reviewed_on
listings ||--o{ reports : reported_on

reservations ||--o{ payments : generates
@enduml
```

## Configuration & Environment Variable Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Application secret key | Generated | Yes |
| `DATABASE_URL` | Database connection URL | `sqlite:///campus_kubo.db` | No |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | None | No |
| `EMAIL_SERVER` | SMTP server | `smtp.gmail.com` | No |
| `EMAIL_PORT` | SMTP port | `587` | No |
| `EMAIL_USERNAME` | SMTP username | None | No |
| `EMAIL_PASSWORD` | SMTP password | None | No |
| `UPLOAD_FOLDER` | File upload directory | `app/storage/data/uploads` | No |
| `MAX_CONTENT_LENGTH` | Max upload size | `16MB` | No |
| `SESSION_TIMEOUT` | Session timeout minutes | `30` | No |

### Configuration Files

#### `config/colors.py`
Contains color scheme definitions for the UI:

```python
COLORS = {
    "primary": "#0078FF",
    "secondary": "#6C757D",
    "success": "#28A745",
    "danger": "#DC3545",
    "warning": "#FFC107",
    "info": "#17A2B8",
    "light": "#F8F9FA",
    "dark": "#343A40",
    "background": "#FFFFFF",
    "surface": "#F8F9FA",
    "text_dark": "#212529",
    "text_muted": "#6C757D",
    "border": "#DEE2E6"
}
```

#### `config/__init__.py`
Application configuration settings:

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///campus_kubo.db'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'storage', 'data', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    SESSION_TIMEOUT = 30  # minutes
```

### API Keys Setup

1. **Google Maps API**:
   - Get API key from Google Cloud Console
   - Enable Maps JavaScript API and Geocoding API
   - Set `GOOGLE_MAPS_API_KEY` environment variable

2. **Email Service**:
   - Configure SMTP settings in environment variables
   - For Gmail: Enable 2FA and use App Passwords

### File Structure

```
config/
├── __init__.py      # Main configuration
├── colors.py        # UI color scheme
└── settings.py      # App settings model
```