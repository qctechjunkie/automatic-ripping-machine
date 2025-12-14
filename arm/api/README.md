# ARM FastAPI Backend

Modern async REST API for Automatic Ripping Machine.

## Architecture

This FastAPI backend replaces the Flask-based UI with a modern async API that provides:

- RESTful endpoints for all ARM operations
- WebSocket support for real-time job progress
- Automatic OpenAPI documentation
- Async database operations
- Proper authentication with JWT tokens
- Environment-based configuration

## Directory Structure

```
arm/api/
├── __init__.py           # Package initialization
├── main.py               # FastAPI application entry point
├── config.py             # Settings management (fixes hardcoded secrets)
├── database.py           # Async SQLAlchemy setup
├── dependencies.py       # FastAPI dependency injection
├── routers/              # API route modules
│   ├── __init__.py
│   ├── jobs.py          # Job management endpoints
│   ├── auth.py          # Authentication endpoints
│   ├── settings.py      # Configuration endpoints
│   ├── logs.py          # Log viewing endpoints
│   ├── drives.py        # Drive management endpoints
│   ├── notifications.py # Notification endpoints
│   └── realtime.py      # WebSocket/SSE endpoints
├── schemas/              # Pydantic models
│   ├── __init__.py
│   ├── job.py           # Job request/response schemas
│   ├── auth.py          # Auth schemas
│   └── ...              # Other schemas
├── services/             # Business logic
│   ├── __init__.py
│   ├── job_service.py   # Job operations
│   ├── metadata_service.py
│   └── log_parser.py
└── websockets/           # Real-time handlers
    ├── __init__.py
    ├── job_progress.py
    └── system_stats.py
```

## Key Components

### main.py

The FastAPI application with:
- Lifespan management (startup/shutdown)
- CORS middleware
- Exception handlers
- Health check endpoints
- Auto-generated documentation

### config.py

Environment-based configuration using Pydantic Settings:
- Replaces hardcoded secrets from Flask version
- Loads from `.env` file or environment variables
- Integrates with existing ARM config (arm.yaml)

**Security Fix:** This addresses the critical issue in `arm/ui/__init__.py:56` where `SECRET_KEY = "Big secret key"` was hardcoded.

### database.py

Async SQLAlchemy 2.0 setup:
- Async engine with connection pooling
- Session management via dependency injection
- SQLite optimizations (WAL mode, pragmas)
- Migration helpers

### dependencies.py

FastAPI dependencies for:
- JWT authentication
- Database sessions
- User validation
- Admin access control

### schemas/

Pydantic models for request/response validation:
- `job.py` - Job CRUD operations
- `auth.py` - Login, registration, tokens
- Type checking and validation
- Automatic OpenAPI schema generation

### routers/

API endpoint modules (to be implemented):
- `jobs.py` - CRUD operations for jobs
- `auth.py` - Login, logout, token refresh
- `settings.py` - Configuration management
- `logs.py` - Log file viewing
- `drives.py` - Drive operations
- `notifications.py` - User notifications
- `realtime.py` - WebSocket endpoints for live updates

### services/

Business logic layer:
- Separates concerns from route handlers
- Reusable across different endpoints
- Easy to test in isolation

## Design Principles

### 1. Separation of Concerns

```
Request → Router → Service → Database
                ↓
            Response Schema
```

- **Routers**: Handle HTTP requests, validate input
- **Services**: Business logic, data operations
- **Schemas**: Request/response validation
- **Database**: Data persistence

### 2. Dependency Injection

```python
@app.get("/jobs")
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = JobService(db)
    return await service.get_jobs()
```

### 3. Async/Await

All database operations use async/await:
- Better concurrency
- Non-blocking I/O
- Scales better under load

### 4. Type Safety

Pydantic schemas ensure:
- Request validation
- Response formatting
- Type checking
- Auto-generated docs

## Configuration

See `.env.example` for all configuration options.

### Required Settings

```bash
SECRET_KEY=your-generated-secret-key-here
```

### Optional Settings

```bash
DATABASE_URL=sqlite+aiosqlite:///path/to/arm.db
DISABLE_LOGIN=false
ALLOWED_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
```

## Running the API

### Development

```bash
# With auto-reload
python -m arm.api.main

# Or using uvicorn
uvicorn arm.api.main:app --reload
```

### Production

```bash
# Multiple workers
uvicorn arm.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Development Workflow

### Adding a New Endpoint

1. **Define Schema** (`schemas/`)
   ```python
   class MyRequest(BaseModel):
       field: str
   ```

2. **Create Service** (`services/`)
   ```python
   class MyService:
       async def do_something(self):
           ...
   ```

3. **Add Router** (`routers/`)
   ```python
   @router.post("/endpoint")
   async def my_endpoint(request: MyRequest):
       ...
   ```

4. **Register Router** (`main.py`)
   ```python
   app.include_router(my_router)
   ```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest arm/api/tests/
```

## Migration from Flask

The FastAPI backend coexists with Flask during migration:

1. Flask serves existing UI at `/`
2. FastAPI serves new API at `/api/*`
3. Gradually migrate frontend to use FastAPI
4. Eventually remove Flask entirely

## Performance Improvements

vs Flask version:

- ✅ Async database queries
- ✅ Database indexes for faster searches
- ✅ WebSocket for real-time updates (vs polling)
- ✅ Better connection pooling
- ✅ Reduced memory usage

## Security Improvements

vs Flask version:

- ✅ No hardcoded secrets
- ✅ Environment-based configuration
- ✅ JWT tokens (vs sessions)
- ✅ Proper CORS configuration
- ✅ Input validation with Pydantic

## Next Steps

1. Implement router modules (jobs, auth, etc.)
2. Create service layer
3. Add WebSocket support
4. Write tests
5. Update frontend to use new API

See `REDESIGN_PLAN.md` for the complete roadmap.
