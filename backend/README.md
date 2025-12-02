# ChatForm Backend

FastAPI backend for the ChatForm validation system.

## Setup

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
Edit `backend/.env` and add your Google Maps API key:
```
GOOGLE_MAPS_API_KEY=your-actual-google-maps-api-key
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

4. **Run the server**:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### POST /api/validate
Validates application data and returns red flags.

**Request body**:
```json
{
  "currentAddress": "123 Main St, Bangkok",
  "companyAddress": "456 Office Rd, Chiang Mai",
  "occupation": "Software Engineer",
  ...
}
```

**Response**:
```json
{
  "red_flags": [
    {
      "rule": "distance_check",
      "message": "Home and work addresses are 685.5km apart (limit: 150km)",
      "affectedFields": ["currentAddress", "companyAddress"]
    }
  ]
}
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── routers/
│   │   └── validation.py    # Validation endpoints
│   ├── services/
│   │   ├── distance_service.py  # Google Geocoding + distance calc
│   │   └── rule_engine.py       # Validation rules
│   └── schemas/
│       └── application.py   # Pydantic models
├── requirements.txt
└── .env
```
