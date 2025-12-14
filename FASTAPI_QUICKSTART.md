# FastAPI Backend - Quick Start Guide

This guide will help you get started with the new FastAPI backend for ARM.

## Prerequisites

- Python 3.8 or higher
- Existing ARM installation with database
- pip or conda package manager

## Installation

### 1. Install Dependencies

```bash
# Install FastAPI backend dependencies
pip install -r requirements_api.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and set your SECRET_KEY
# nano .env
```

**Important:** Replace the `SECRET_KEY` with the generated value. This fixes the hardcoded secret security issue from the Flask version.

### 3. Add Database Indexes (Recommended)

For optimal performance, add indexes to your existing database:

```bash
python scripts/add_database_indexes.py
```

This will:
- Create indexes for faster queries
- Set up full-text search
- Create a backup of your database
- Improve performance for large datasets (3000+ jobs)

## Running the FastAPI Server

### Development Mode (with auto-reload)

```bash
# Run from project root
cd arm
python -m api.main

# Or use uvicorn directly
uvicorn arm.api.main:app --reload --port 8000
```

The server will start on `http://localhost:8000`

### Production Mode

```bash
# Single worker
uvicorn arm.api.main:app --host 0.0.0.0 --port 8000

# Multiple workers (better performance)
uvicorn arm.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Accessing the API

Once the server is running:

- **API Documentation (Swagger UI):** http://localhost:8000/api/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/api/redoc
- **OpenAPI Schema:** http://localhost:8000/api/openapi.json
- **Health Check:** http://localhost:8000/api/health

## Configuration Options

All configuration is done via environment variables in `.env` file:

### Security Settings

```bash
SECRET_KEY=your-generated-secret-key    # REQUIRED for production
ALGORITHM=HS256                         # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=60          # Token expiration
```

### Database Settings

```bash
DATABASE_URL=sqlite+aiosqlite:///arm.db  # Override database location
# If not set, reads from arm.yaml config
```

### Server Settings

```bash
HOST=0.0.0.0                            # Server host
PORT=8000                               # Server port
WORKERS=4                               # Number of workers
LOG_LEVEL=INFO                          # Logging level
```

### Authentication

```bash
DISABLE_LOGIN=false                     # Disable authentication
```

### CORS Settings

```bash
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/api/health

# Get API info
curl http://localhost:8000/api/info

# Get jobs (authentication required unless DISABLE_LOGIN=true)
curl http://localhost:8000/api/jobs
```

### Using the Swagger UI

1. Open http://localhost:8000/api/docs
2. Click "Try it out" on any endpoint
3. Execute the request
4. View the response

## Next Steps

After the basic setup:

1. **Implement API Routers** - Create the job, auth, settings endpoints
2. **Set up WebSocket** - For real-time job progress updates
3. **Create Services** - Business logic layer
4. **Add Tests** - Unit and integration tests
5. **Update Frontend** - Connect to new API

See `REDESIGN_PLAN.md` for the complete implementation roadmap.

## Troubleshooting

### Database Connection Issues

```bash
# Check database path
python -c "import arm.config.config as cfg; print(cfg.arm_config['DBFILE'])"

# Test database connection
python arm/api/database.py
```

### Secret Key Not Set

If you see warnings about secret keys:

```bash
# Generate and set in .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Port Already in Use

```bash
# Use a different port
uvicorn arm.api.main:app --port 8001

# Or kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux:
lsof -ti:8000 | xargs kill -9
```

### Import Errors

```bash
# Make sure you're in the project root
cd /path/to/automatic-ripping-machine

# Install dependencies
pip install -r requirements_api.txt
```

## Comparison with Flask Version

### What's Fixed

✅ **Security:** No more hardcoded secrets (arm/ui/__init__.py:56-61)
✅ **Performance:** Database indexes for faster queries
✅ **Modern:** Async/await support for better concurrency
✅ **Documentation:** Automatic OpenAPI/Swagger docs
✅ **Type Safety:** Pydantic validation for all inputs

### What's New

🆕 **WebSocket Support:** Real-time job progress updates
🆕 **RESTful API:** Proper HTTP methods and endpoints
🆕 **Better Architecture:** Separation of concerns (routers/services/schemas)
🆕 **Environment Config:** Proper secrets management
🆕 **Full-Text Search:** Fast text searching with FTS5

## Support

- Report issues: https://github.com/automatic-ripping-machine/automatic-ripping-machine/issues
- Full redesign plan: See `REDESIGN_PLAN.md`
- Architecture details: See `arm/api/README.md`
