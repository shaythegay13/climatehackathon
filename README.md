# NYC Indoor Air Quality Dashboard - Backend

This is the backend service for the NYC Indoor Air Quality Dashboard, built with FastAPI and SQLAlchemy. It provides APIs for collecting, storing, and querying indoor air quality data across different locations in New York City.

## Features

- **Sensor Data Collection**: Endpoints to submit air quality sensor readings including PM2.5, CO2, VOCs, temperature, humidity, and mold risk.
- **Location-based Data**: All sensor readings are associated with specific NYC zipcodes and boroughs.
- **Real-time Monitoring**: APIs to fetch the latest sensor readings and statistics.
- **Public Health Integration**: Store and retrieve public health data like asthma rates by location.
- **Data Analysis**: Endpoints to get aggregated statistics and trends over time.
- **Alerts & Recommendations (Step 2)**: Threshold-based alerting and DIY recommendations.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (SQLite for development)
- **ORM**: SQLAlchemy
- **Data Validation**: Pydantic
- **API Documentation**: Swagger UI & ReDoc (automatically generated)

## Prerequisites

- Python 3.8+
- PostgreSQL (for production)
- pip (Python package manager)

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nyc-air-quality-dashboard/backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Update the database connection string and other settings as needed

5. **Initialize the database**
   ```bash
   # This will create all necessary tables
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Production
For production, use a production-grade ASGI server like Uvicorn with Gunicorn:
```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app
```

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Step 2: Core APIs and Behavior

All Step-2 endpoints are prefixed with `/api/v1`.

- `POST /api/v1/sensor-ingest`
  - Body: `{ zipcode, borough, timestamp?, pm25?, co2?, tvoc?, humidity?, temperature?, mold_risk? }`
  - Behavior: Persists the reading, evaluates thresholds, and stores generated alerts.

- `GET /api/v1/alerts?zipcode=&time_window_hours=24`
  - Returns active alerts within the time window with severity, reason, timestamp, and location metadata.

- `GET /api/v1/context?zipcode=&year=`
  - Returns mock overlays for now (e.g., `asthma_rate`).

- `GET /api/v1/recommendations?zipcode=&latest=true`
  - Returns DIY actions if the latest reading for the zipcode triggers alerts, otherwise `no action needed`.

### Alert Thresholds

- PM2.5: `> 35 µg/m³`
- CO₂: `> 1200 ppm`
- TVOC: `> 200 ppb`
- Humidity: `< 30%` or `> 60%`
- Mold risk: `>= 0.6`

Threshold logic is implemented in `app/services/alert_engine.py`.

## Example API Usage

### Submit a Sensor Reading
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/sensor-ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "zipcode": "10001",
    "borough": "Manhattan",
    "pm25": 12.5,
    "co2": 850,
    "tvoc": 120.5,
    "temperature": 22.5,
    "humidity": 45.0,
    "mold_risk": 0.3
  }'
```

### Get Alerts (last 24h)
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/alerts?zipcode=10001&time_window_hours=24' \
  -H 'accept: application/json'
```

### Get Recommendations
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/recommendations?zipcode=10001' \
  -H 'accept: application/json'
```

### Get Context (mock overlays)
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/context?zipcode=10001&year=2023' \
  -H 'accept: application/json'
```

## Database Schema

### Locations
- `id` (Integer, Primary Key)
- `zipcode` (String, Unique)
- `borough` (String)
- `latitude` (Float, Nullable)
- `longitude` (Float, Nullable)

### SensorReadings
- `id` (Integer, Primary Key)
- `location_id` (Integer, Foreign Key to Locations.id)
- `timestamp` (DateTime)
- `pm25` (Float, μg/m³)
- `co2` (Float, ppm)
- `tvoc` (Float, ppb)
- `temperature` (Float, °C)
- `humidity` (Float, %)
- `mold_risk` (Float, 0-1 scale)

### Alerts
- `id` (Integer, Primary Key)
- `location_id` (FK to Locations.id)
- `reading_id` (FK to SensorReadings.id)
- `created_at` (DateTime)
- `metric` (String)
- `threshold` (Float)
- `value` (Float)
- `severity` (String)
- `message` (String)

### Overlays
- `id` (Integer, Primary Key)
- `location_id` (FK to Locations.id)
- `type` (String)
- `year` (Integer)
- `value` (Float)
- `meta` (JSON)

### PublicHealthData
- `id` (Integer, Primary Key)
- `location_id` (Integer, Foreign Key to Locations.id)
- `year` (Integer)
- `asthma_rate` (Float, per 10,000 people)
- `emergency_visits` (Integer)

## Simulator

Use the provided simulator to generate realistic random readings and post them to `/api/v1/sensor-ingest` on an interval.

```bash
# Ensure server is running on localhost:8000
python scripts/simulator.py
```

Configure via `.env`:

- `SIMULATOR_BASE_URL` (default `http://localhost:8000`)
- `SIMULATOR_ZIPCODES` (comma-separated list)
- `SIMULATOR_BOROUGH`
- `SIMULATOR_INTERVAL_SECONDS`

## Database Migrations (Alembic)

This repo includes Alembic to manage schema changes for Step 3 tables (`households`, `household_sensor_readings`, `household_alerts`, `health_context`).

Files to note:

- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/20250927_01_step3_schema.py`

Run migrations:

```bash
# Ensure DATABASE_URL is set (or present in .env). Examples:
# export DATABASE_URL=sqlite:///./air_quality.db
# export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/air_quality_db

# Upgrade to latest
alembic upgrade head

# Downgrade one revision (if needed)
alembic downgrade -1
```

Notes:

- The migration creates new Step 3-specific tables with names that won't conflict with existing app tables:
  - `households`
  - `household_sensor_readings`
  - `household_alerts`
  - `health_context`
- Indexes are created for common query patterns (e.g., `(household_id, timestamp)` on readings and alerts).
- For SQLite, triggers requiring `plpgsql` are skipped automatically.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
