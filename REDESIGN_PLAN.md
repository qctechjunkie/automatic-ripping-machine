# Automatic Ripping Machine - Web Interface Redesign Plan

**Created:** 2025-12-14
**Status:** Planning Phase
**Primary Goal:** Modernize web interface with Tailwind CSS, improve performance, and enhance user experience

---

## Executive Summary

The current web interface uses Flask + jQuery + Bootstrap 4. This plan outlines three redesign approaches with different priorities, with the initial focus on **Performance & Scalability** followed by UI modernization.

**Current Stack:**
- Backend: Flask 3.x with SQLAlchemy
- Frontend: jQuery 3.5.1 + Bootstrap 4.x
- Database: SQLite
- Server: Waitress WSGI

**Target Stack (Phase 1 - Performance):**
- Backend: FastAPI with SQLAlchemy 2.0
- Frontend: jQuery + Bootstrap 4 (temporary) → React + Tailwind (Phase 2)
- Database: SQLite with optimizations
- Server: Uvicorn with WebSocket support

---

## Three Redesign Approaches

### Option 1: Modern Look & Feel (Incremental)
**Timeline:** Fastest (4-6 weeks)
**Risk:** Low
**Best for:** Quick visual improvements without major architecture changes

- Replace Bootstrap 4 with Tailwind CSS
- Keep jQuery and Flask backend
- Refactor dark mode using Tailwind's built-in support
- Improve component styling and responsiveness
- Minimal API changes

### Option 2: Full Rewrite (Comprehensive)
**Timeline:** Longest (12-16 weeks)
**Risk:** High
**Best for:** Long-term maintainability and modern development experience

- Complete frontend rewrite with React/Vue + Tailwind
- Migrate Flask to FastAPI
- Implement proper REST API design
- Add TypeScript for type safety
- Modern build pipeline (Vite)
- Comprehensive testing suite

### Option 3: Performance & Scalability (Balanced) ⭐ **CHOSEN**
**Timeline:** Medium (8-12 weeks)
**Risk:** Medium
**Best for:** Addressing technical debt while modernizing incrementally

- Migrate to FastAPI backend (async, WebSocket support)
- Implement real-time updates (SSE/WebSockets)
- Optimize database queries and add indexing
- Refactor API to RESTful design
- Improve search & filtering
- **Then** migrate frontend to React + Tailwind

---

## Phase 1: Performance & Scalability (START HERE)

### 1.1 Backend Migration: Flask → FastAPI

**Why FastAPI?**
- Native async/await support for real-time features
- Automatic OpenAPI documentation
- Built-in WebSocket support
- Faster performance (ASGI vs WSGI)
- Modern Python type hints
- Easy migration path from Flask

#### Implementation Steps

**1.1.1 Project Setup**
```bash
# New dependencies
pip install fastapi uvicorn[standard] python-socketio python-multipart
pip install sqlalchemy[asyncio] aiosqlite  # Async SQLAlchemy
pip install python-jose[cryptography] passlib[bcrypt]  # Auth
pip install sse-starlette  # Server-Sent Events
```

**1.1.2 Directory Structure**
```
arm/
├── api/                          # New FastAPI backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── dependencies.py           # Dependency injection
│   ├── middleware.py             # CORS, auth, error handling
│   ├── config.py                 # Settings (replace hardcoded secrets)
│   ├── routers/                  # API route modules
│   │   ├── __init__.py
│   │   ├── jobs.py              # Job management endpoints
│   │   ├── auth.py              # Authentication
│   │   ├── settings.py          # Configuration
│   │   ├── logs.py              # Log viewing
│   │   ├── drives.py            # Drive management
│   │   ├── notifications.py     # Notification system
│   │   └── realtime.py          # WebSocket/SSE endpoints
│   ├── schemas/                  # Pydantic models
│   │   ├── __init__.py
│   │   ├── job.py
│   │   ├── user.py
│   │   ├── notification.py
│   │   └── settings.py
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── job_service.py
│   │   ├── metadata_service.py
│   │   ├── log_parser.py
│   │   └── notification_service.py
│   └── websockets/               # Real-time handlers
│       ├── __init__.py
│       ├── job_progress.py
│       └── system_stats.py
├── ui/                           # Legacy Flask UI (temporary)
└── models/                       # Shared SQLAlchemy models
```

**1.1.3 Core FastAPI Setup**
```python
# arm/api/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .config import settings
from .routers import jobs, auth, settings_router, logs, drives, notifications, realtime
from .middleware import auth_middleware, error_handler_middleware
from .database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Close connections
    await engine.dispose()

app = FastAPI(
    title="Automatic Ripping Machine API",
    description="REST API for ARM disc ripping automation",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(drives.router, prefix="/api/drives", tags=["drives"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(realtime.router, prefix="/api/realtime", tags=["realtime"])

# Static files (for frontend)
app.mount("/static", StaticFiles(directory="arm/ui/static"), name="static")

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0"}
```

**1.1.4 Configuration Management (Fix Security Issues)**
```python
# arm/api/config.py
from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate random key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///arm.db"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ARM Configuration
    ARM_CONFIG_PATH: str = "/etc/arm/config/arm.yaml"
    RAW_PATH: str = "/mnt/raw"
    COMPLETED_PATH: str = "/mnt/completed"
    LOG_PATH: str = "/mnt/logs"

    # Features
    DISABLE_LOGIN: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**1.1.5 Database Optimization**
```python
# arm/models/job.py (enhance existing model)
from sqlalchemy import Index, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = 'job'

    job_id = Column(Integer, primary_key=True)
    crc_id = Column(String(63), index=True)  # Add index
    title = Column(String(256), index=True)  # Add index
    status = Column(String(32), index=True)  # Add index for filtering
    video_type = Column(String(25), index=True)
    created_date = Column(DateTime, index=True)  # Add index for sorting
    updated_date = Column(DateTime, index=True)
    # ... other columns

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_date'),
        Index('idx_title_status', 'title', 'status'),
        Index('idx_video_type_status', 'video_type', 'status'),
    )
```

**Migration Script:**
```python
# scripts/add_database_indexes.py
from sqlalchemy import create_engine, Index
from arm.models import Job

engine = create_engine('sqlite:///arm.db')

# Add indexes to existing database
indexes = [
    Index('idx_status', Job.status),
    Index('idx_title', Job.title),
    Index('idx_crc_id', Job.crc_id),
    Index('idx_created_date', Job.created_date),
    Index('idx_status_created', Job.status, Job.created_date),
]

with engine.begin() as conn:
    for index in indexes:
        try:
            index.create(conn)
            print(f"Created index: {index.name}")
        except Exception as e:
            print(f"Index {index.name} already exists or error: {e}")
```

### 1.2 RESTful API Design

**Current Problem:** Single `/json?mode=X` endpoint is not RESTful

**New API Structure:**

```python
# arm/api/routers/jobs.py
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..schemas.job import JobResponse, JobCreate, JobUpdate, JobFilter
from ..services.job_service import JobService
from ..dependencies import get_db, get_current_user

router = APIRouter()

# GET /api/jobs - List jobs with filtering and pagination
@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status: success/fail/active"),
    video_type: Optional[str] = Query(None, description="Filter by type: movie/tv"),
    search: Optional[str] = Query(None, description="Search in title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("created_date", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieve jobs with advanced filtering, searching, and pagination.

    - **status**: Filter by job status
    - **video_type**: Filter by media type
    - **search**: Full-text search in title and notes
    - **skip**: Number of records to skip (offset)
    - **limit**: Maximum records to return
    - **sort_by**: Field to sort by
    - **sort_desc**: Sort in descending order
    """
    service = JobService(db)
    filters = JobFilter(
        status=status,
        video_type=video_type,
        search=search
    )
    return await service.get_jobs(filters, skip, limit, sort_by, sort_desc)

# GET /api/jobs/{job_id} - Get single job details
@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed information for a specific job."""
    service = JobService(db)
    job = await service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# PUT /api/jobs/{job_id} - Update job
@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update job information (title, metadata, parameters)."""
    service = JobService(db)
    updated_job = await service.update_job(job_id, job_update)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return updated_job

# DELETE /api/jobs/{job_id} - Delete job
@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    delete_files: bool = Query(False, description="Also delete physical files"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a job from the database and optionally its files."""
    service = JobService(db)
    success = await service.delete_job(job_id, delete_files)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return None

# POST /api/jobs/{job_id}/abandon - Kill running job
@router.post("/{job_id}/abandon", response_model=JobResponse)
async def abandon_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Kill a running job process."""
    service = JobService(db)
    job = await service.abandon_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Kill process in background
    background_tasks.add_task(service.kill_job_process, job.pid)
    return job

# GET /api/jobs/{job_id}/tracks - Get disc tracks
@router.get("/{job_id}/tracks")
async def get_job_tracks(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all tracks for a disc job."""
    service = JobService(db)
    tracks = await service.get_tracks(job_id)
    return tracks

# GET /api/jobs/{job_id}/log - Get job log with progress
@router.get("/{job_id}/log")
async def get_job_log(
    job_id: int,
    follow: bool = Query(False, description="Stream log in real-time"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get job log content with parsed progress information.
    Use follow=true for real-time streaming (SSE).
    """
    service = JobService(db)
    if follow:
        # Return SSE stream
        return await service.stream_log(job_id)
    else:
        # Return full log
        return await service.get_log(job_id)

# GET /api/jobs/active - Get currently running jobs
@router.get("/active/list", response_model=List[JobResponse])
async def get_active_jobs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all currently active/running jobs."""
    service = JobService(db)
    return await service.get_active_jobs()

# POST /api/jobs/search - Advanced search
@router.post("/search", response_model=List[JobResponse])
async def search_jobs(
    search_params: JobSearchParams,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Advanced job search with multiple criteria.
    Supports date ranges, multiple statuses, regex patterns.
    """
    service = JobService(db)
    return await service.advanced_search(search_params)
```

**Pydantic Schemas:**
```python
# arm/api/schemas/job.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JobBase(BaseModel):
    title: Optional[str] = None
    year: Optional[str] = None
    video_type: Optional[str] = None
    poster_url: Optional[str] = None
    hasnicetitle: Optional[bool] = None

class JobCreate(JobBase):
    crc_id: str
    disc_label: str

class JobUpdate(JobBase):
    status: Optional[str] = None
    config_id: Optional[int] = None

class JobResponse(JobBase):
    job_id: int
    crc_id: str
    status: str
    created_date: datetime
    updated_date: Optional[datetime] = None
    progress: Optional[float] = None

    class Config:
        from_attributes = True

class JobFilter(BaseModel):
    status: Optional[str] = None
    video_type: Optional[str] = None
    search: Optional[str] = None

class JobSearchParams(BaseModel):
    query: Optional[str] = None
    statuses: Optional[List[str]] = None
    video_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
```

### 1.3 Real-Time Job Progress

**Problem:** Current implementation polls `/json?mode=...` every few seconds

**Solution:** WebSocket connection for live updates

```python
# arm/api/routers/realtime.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import asyncio
import json
from ..services.job_service import JobService
from ..dependencies import get_db

router = APIRouter()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "jobs": set(),
            "system": set(),
        }

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        self.active_connections[channel].discard(websocket)

    async def broadcast(self, message: dict, channel: str):
        """Broadcast message to all clients on a channel."""
        dead_connections = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        for connection in dead_connections:
            self.active_connections[channel].discard(connection)

manager = ConnectionManager()

@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time job updates.

    Sends updates when:
    - Job status changes
    - Progress updates
    - New jobs detected
    - Jobs completed/failed
    """
    await manager.connect(websocket, "jobs")
    try:
        # Send initial data
        async with get_db() as db:
            service = JobService(db)
            active_jobs = await service.get_active_jobs()
            await websocket.send_json({
                "type": "initial",
                "jobs": [job.dict() for job in active_jobs]
            })

        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle client requests (like pause/resume)
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, "jobs")

# Background task to monitor job progress
async def job_progress_monitor():
    """
    Background task that monitors log files and broadcasts progress updates.
    Should be started on application startup.
    """
    from ..services.log_parser import LogParser

    while True:
        try:
            async with get_db() as db:
                service = JobService(db)
                active_jobs = await service.get_active_jobs()

                for job in active_jobs:
                    # Parse log file for progress
                    log_path = f"/mnt/logs/{job.crc_id}.log"
                    parser = LogParser(log_path)
                    progress = await parser.get_progress()

                    if progress != job.progress:
                        # Progress changed, update DB and broadcast
                        await service.update_progress(job.job_id, progress)
                        await manager.broadcast({
                            "type": "progress_update",
                            "job_id": job.job_id,
                            "progress": progress,
                            "stage": parser.current_stage
                        }, "jobs")
        except Exception as e:
            print(f"Error in progress monitor: {e}")

        await asyncio.sleep(2)  # Check every 2 seconds

# Alternative: Server-Sent Events (simpler, one-way)
from sse_starlette.sse import EventSourceResponse

@router.get("/sse/jobs")
async def sse_jobs(db = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Server-Sent Events endpoint for job updates.
    Simpler alternative to WebSocket, browser-native.
    """
    async def event_generator():
        service = JobService(db)
        last_update = None

        while True:
            # Check for updates
            jobs = await service.get_active_jobs()
            current_state = {job.job_id: job.progress for job in jobs}

            if current_state != last_update:
                yield {
                    "event": "jobs_update",
                    "data": json.dumps([job.dict() for job in jobs])
                }
                last_update = current_state

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
```

**Frontend Integration (Temporary jQuery version):**
```javascript
// arm/ui/static/js/realtimeJobs.js
class JobMonitor {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/realtime/ws/jobs`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(message) {
        switch (message.type) {
            case 'initial':
                this.renderJobs(message.jobs);
                break;
            case 'progress_update':
                this.updateJobProgress(message.job_id, message.progress, message.stage);
                break;
            case 'job_completed':
                this.handleJobCompleted(message.job_id);
                break;
            case 'new_job':
                this.addNewJob(message.job);
                break;
            case 'heartbeat':
                // Keep-alive
                break;
        }
    }

    updateJobProgress(jobId, progress, stage) {
        const progressBar = $(`#job-${jobId} .progress-bar`);
        const stageText = $(`#job-${jobId} .stage-text`);

        progressBar.css('width', `${progress}%`);
        progressBar.attr('aria-valuenow', progress);
        progressBar.text(`${progress.toFixed(1)}%`);
        stageText.text(stage);
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${delay}ms...`);
            setTimeout(() => this.connect(), delay);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Initialize on page load
const jobMonitor = new JobMonitor();
$(document).ready(() => {
    jobMonitor.connect();
});

// Clean up on page unload
$(window).on('beforeunload', () => {
    jobMonitor.disconnect();
});
```

### 1.4 Advanced Search & Filtering

**Problem:** Database page loads all 3000+ jobs, searches are inefficient

**Solution:** Backend search with FTS, frontend virtualization

```python
# arm/api/services/job_service.py
from sqlalchemy import select, or_, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models import Job, Track
from ..schemas.job import JobFilter, JobSearchParams

class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_jobs(
        self,
        filters: JobFilter,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "created_date",
        sort_desc: bool = True
    ) -> List[Job]:
        """
        Get jobs with filtering, pagination, and sorting.
        Uses indexes for efficient queries.
        """
        query = select(Job)

        # Apply filters
        conditions = []
        if filters.status:
            conditions.append(Job.status == filters.status)
        if filters.video_type:
            conditions.append(Job.video_type == filters.video_type)
        if filters.search:
            # Full-text search in title
            search_pattern = f"%{filters.search}%"
            conditions.append(
                or_(
                    Job.title.ilike(search_pattern),
                    Job.year.ilike(search_pattern),
                    Job.disc_label.ilike(search_pattern)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Sorting
        sort_column = getattr(Job, sort_by, Job.created_date)
        if sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_total_count(self, filters: JobFilter) -> int:
        """Get total count for pagination."""
        query = select(func.count(Job.job_id))

        conditions = []
        if filters.status:
            conditions.append(Job.status == filters.status)
        if filters.video_type:
            conditions.append(Job.video_type == filters.video_type)
        if filters.search:
            search_pattern = f"%{filters.search}%"
            conditions.append(
                or_(
                    Job.title.ilike(search_pattern),
                    Job.year.ilike(search_pattern),
                    Job.disc_label.ilike(search_pattern)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar()

    async def advanced_search(self, params: JobSearchParams) -> List[Job]:
        """
        Advanced search with multiple criteria.
        """
        query = select(Job)
        conditions = []

        # Text search
        if params.query:
            search_pattern = f"%{params.query}%"
            conditions.append(
                or_(
                    Job.title.ilike(search_pattern),
                    Job.year.ilike(search_pattern),
                    Job.disc_label.ilike(search_pattern)
                )
            )

        # Multiple statuses
        if params.statuses:
            conditions.append(Job.status.in_(params.statuses))

        # Multiple video types
        if params.video_types:
            conditions.append(Job.video_type.in_(params.video_types))

        # Date range
        if params.date_from:
            conditions.append(Job.created_date >= params.date_from)
        if params.date_to:
            conditions.append(Job.created_date <= params.date_to)

        # Year range
        if params.min_year:
            conditions.append(Job.year >= str(params.min_year))
        if params.max_year:
            conditions.append(Job.year <= str(params.max_year))

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Job.created_date.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

# Enhanced endpoint with count
@router.get("/api/jobs", response_model=JobListResponse)
async def list_jobs_with_count(...):
    service = JobService(db)
    jobs = await service.get_jobs(filters, skip, limit, sort_by, sort_desc)
    total = await service.get_total_count(filters)

    return JobListResponse(
        jobs=jobs,
        total=total,
        skip=skip,
        limit=limit
    )
```

**Frontend: Virtual Scrolling (Temporary jQuery + virtual-list)**
```javascript
// arm/ui/static/js/virtualJobList.js
// For large datasets, load data in chunks as user scrolls
class VirtualJobList {
    constructor(containerId, fetchFunction) {
        this.container = $(`#${containerId}`);
        this.fetchFunction = fetchFunction;
        this.currentPage = 0;
        this.pageSize = 50;
        this.loading = false;
        this.allLoaded = false;

        this.setupScrollListener();
    }

    setupScrollListener() {
        this.container.on('scroll', () => {
            if (this.shouldLoadMore()) {
                this.loadMore();
            }
        });
    }

    shouldLoadMore() {
        if (this.loading || this.allLoaded) return false;

        const scrollTop = this.container.scrollTop();
        const scrollHeight = this.container[0].scrollHeight;
        const clientHeight = this.container.height();

        // Load when 200px from bottom
        return scrollTop + clientHeight >= scrollHeight - 200;
    }

    async loadMore() {
        this.loading = true;
        this.showLoadingIndicator();

        try {
            const skip = this.currentPage * this.pageSize;
            const response = await this.fetchFunction(skip, this.pageSize);

            if (response.jobs.length === 0) {
                this.allLoaded = true;
            } else {
                this.appendJobs(response.jobs);
                this.currentPage++;
            }
        } catch (error) {
            console.error('Error loading jobs:', error);
        } finally {
            this.loading = false;
            this.hideLoadingIndicator();
        }
    }

    appendJobs(jobs) {
        jobs.forEach(job => {
            const jobCard = this.createJobCard(job);
            this.container.append(jobCard);
        });
    }
}

// Usage
async function fetchJobs(skip, limit) {
    const params = new URLSearchParams({
        skip,
        limit,
        status: $('#statusFilter').val(),
        search: $('#searchInput').val()
    });

    const response = await fetch(`/api/jobs?${params}`);
    return response.json();
}

const jobList = new VirtualJobList('jobListContainer', fetchJobs);
```

### 1.5 Database Schema Enhancements

**Add full-text search support:**
```sql
-- migrations/001_add_fts.sql
-- SQLite FTS5 virtual table for fast text search
CREATE VIRTUAL TABLE IF NOT EXISTS job_fts USING fts5(
    job_id UNINDEXED,
    title,
    year,
    disc_label,
    content='job',
    content_rowid='job_id'
);

-- Populate FTS table
INSERT INTO job_fts(job_id, title, year, disc_label)
SELECT job_id, title, year, label FROM job;

-- Triggers to keep FTS in sync
CREATE TRIGGER job_ai AFTER INSERT ON job BEGIN
    INSERT INTO job_fts(job_id, title, year, disc_label)
    VALUES (new.job_id, new.title, new.year, new.label);
END;

CREATE TRIGGER job_ad AFTER DELETE ON job BEGIN
    DELETE FROM job_fts WHERE job_id = old.job_id;
END;

CREATE TRIGGER job_au AFTER UPDATE ON job BEGIN
    UPDATE job_fts SET
        title = new.title,
        year = new.year,
        disc_label = new.label
    WHERE job_id = new.job_id;
END;
```

**Query FTS table:**
```python
async def fts_search(self, query: str) -> List[Job]:
    """Full-text search using SQLite FTS5."""
    fts_query = text("""
        SELECT j.* FROM job j
        INNER JOIN job_fts fts ON j.job_id = fts.job_id
        WHERE job_fts MATCH :query
        ORDER BY rank
        LIMIT 100
    """)

    result = await self.db.execute(fts_query, {"query": query})
    return result.scalars().all()
```

---

## Phase 2: Frontend Modernization (React + Tailwind)

**Status:** Planned after Phase 1 completion

### 2.1 Technology Stack

**Core:**
- React 18+ (with hooks and concurrent features)
- TypeScript for type safety
- Vite for blazing-fast builds
- Tailwind CSS 3.x for styling

**State Management:**
- TanStack Query (React Query) for server state
- Zustand for client state
- WebSocket integration for real-time updates

**UI Components:**
- shadcn/ui (Radix UI + Tailwind)
- Headless UI for accessible components
- Lucide React for icons

**Routing:**
- React Router v6
- Suspense-based code splitting

**Forms:**
- React Hook Form with Zod validation

### 2.2 Project Structure

```
frontend/
├── src/
│   ├── app/                      # Main app setup
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── providers.tsx
│   ├── components/               # Reusable components
│   │   ├── ui/                   # shadcn components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── DarkModeToggle.tsx
│   │   ├── job/
│   │   │   ├── JobCard.tsx
│   │   │   ├── JobProgressBar.tsx
│   │   │   ├── JobFilters.tsx
│   │   │   └── JobDetails.tsx
│   │   └── common/
│   │       ├── SearchBar.tsx
│   │       ├── Pagination.tsx
│   │       └── LoadingSpinner.tsx
│   ├── features/                 # Feature-based organization
│   │   ├── jobs/
│   │   │   ├── hooks/
│   │   │   │   ├── useJobs.ts
│   │   │   │   ├── useJobDetails.ts
│   │   │   │   └── useJobActions.ts
│   │   │   ├── api/
│   │   │   │   └── jobsApi.ts
│   │   │   ├── types/
│   │   │   │   └── job.types.ts
│   │   │   └── pages/
│   │   │       ├── JobListPage.tsx
│   │   │       ├── JobDetailPage.tsx
│   │   │       └── ActiveRipsPage.tsx
│   │   ├── settings/
│   │   ├── logs/
│   │   └── auth/
│   ├── lib/                      # Utilities
│   │   ├── api.ts                # API client setup
│   │   ├── websocket.ts          # WebSocket manager
│   │   └── utils.ts
│   ├── hooks/                    # Global hooks
│   │   ├── useWebSocket.ts
│   │   ├── useRealTimeJobs.ts
│   │   └── useLocalStorage.ts
│   └── styles/
│       └── globals.css           # Tailwind imports
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### 2.3 Tailwind Configuration

```javascript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class', // Use class-based dark mode
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ARM brand colors
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          // ... rest of scale
          900: '#0c4a6e',
        },
        // Status colors
        success: {
          DEFAULT: '#10b981',
          light: '#34d399',
          dark: '#059669',
        },
        error: {
          DEFAULT: '#ef4444',
          light: '#f87171',
          dark: '#dc2626',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fbbf24',
          dark: '#d97706',
        },
        // Dark mode background
        dark: {
          bg: '#1a1a1a',
          card: '#2d2d2d',
          border: '#404040',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
} satisfies Config
```

```css
/* src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;

    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;

    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;

    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;

    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;

    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;

    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;

    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;

    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;

    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;

    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;

    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;

    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;

    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;

    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 2.4 Core Components

**Job Card Component:**
```tsx
// src/components/job/JobCard.tsx
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Play, StopCircle, Trash2 } from 'lucide-react';
import { Job } from '@/features/jobs/types/job.types';
import { cn } from '@/lib/utils';

interface JobCardProps {
  job: Job;
  onView: (jobId: number) => void;
  onDelete: (jobId: number) => void;
  onAbandon?: (jobId: number) => void;
}

export function JobCard({ job, onView, onDelete, onAbandon }: JobCardProps) {
  const isActive = job.status === 'active' || job.status === 'processing';

  const statusColors = {
    success: 'bg-green-500',
    fail: 'bg-red-500',
    active: 'bg-blue-500',
    processing: 'bg-yellow-500',
  };

  return (
    <Card className={cn(
      "hover:shadow-lg transition-shadow",
      isActive && "border-blue-500 border-2"
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-bold">
          {job.title || job.disc_label || 'Unknown Title'}
        </CardTitle>
        <Badge className={statusColors[job.status] || 'bg-gray-500'}>
          {job.status}
        </Badge>
      </CardHeader>

      <CardContent>
        {job.poster_url && (
          <img
            src={job.poster_url}
            alt={job.title}
            className="w-full h-48 object-cover rounded-md mb-4"
          />
        )}

        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex justify-between">
            <span>Type:</span>
            <span className="font-medium">{job.video_type || 'Unknown'}</span>
          </div>
          <div className="flex justify-between">
            <span>Year:</span>
            <span className="font-medium">{job.year || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span>CRC ID:</span>
            <span className="font-mono text-xs">{job.crc_id}</span>
          </div>
        </div>

        {isActive && job.progress !== undefined && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span className="font-medium">{job.progress.toFixed(1)}%</span>
            </div>
            <Progress value={job.progress} className="h-2" />
            {job.stage && (
              <p className="text-xs text-muted-foreground">{job.stage}</p>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onView(job.job_id)}
        >
          View Details
        </Button>

        <div className="flex gap-2">
          {isActive && onAbandon && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onAbandon(job.job_id)}
            >
              <StopCircle className="w-4 h-4 mr-1" />
              Stop
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(job.job_id)}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
```

**Real-Time Hook:**
```tsx
// src/hooks/useRealTimeJobs.ts
import { useEffect, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Job } from '@/features/jobs/types/job.types';

export function useRealTimeJobs() {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/realtime/ws/jobs`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Reconnect after delay
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          // Reinitialize
        }
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'initial':
        // Update active jobs cache
        queryClient.setQueryData(['jobs', 'active'], message.jobs);
        break;

      case 'progress_update':
        // Update specific job in cache
        queryClient.setQueryData(
          ['jobs', 'active'],
          (old: Job[] | undefined) => {
            if (!old) return old;
            return old.map(job =>
              job.job_id === message.job_id
                ? { ...job, progress: message.progress, stage: message.stage }
                : job
            );
          }
        );
        break;

      case 'job_completed':
        // Invalidate queries to refetch
        queryClient.invalidateQueries(['jobs']);
        break;

      case 'new_job':
        // Add new job to cache
        queryClient.setQueryData(
          ['jobs', 'active'],
          (old: Job[] | undefined) => {
            if (!old) return [message.job];
            return [...old, message.job];
          }
        );
        break;
    }
  };

  return { isConnected };
}
```

**Jobs Page:**
```tsx
// src/features/jobs/pages/JobListPage.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { JobCard } from '@/components/job/JobCard';
import { SearchBar } from '@/components/common/SearchBar';
import { Pagination } from '@/components/common/Pagination';
import { Select } from '@/components/ui/select';
import { useRealTimeJobs } from '@/hooks/useRealTimeJobs';
import { fetchJobs } from '../api/jobsApi';

export function JobListPage() {
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState<string>('');
  const [search, setSearch] = useState('');

  // Connect to real-time updates
  const { isConnected } = useRealTimeJobs();

  // Fetch jobs with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs', { page, status, search }],
    queryFn: () => fetchJobs({ skip: page * 50, limit: 50, status, search }),
    keepPreviousData: true,
  });

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Jobs</h1>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-muted-foreground">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search jobs..."
          className="flex-1"
        />
        <Select value={status} onValueChange={setStatus}>
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="fail">Failed</option>
          <option value="active">Active</option>
        </Select>
      </div>

      {/* Job Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Skeleton cards */}
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-96 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center text-red-500">Error loading jobs</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.jobs.map((job) => (
              <JobCard
                key={job.job_id}
                job={job}
                onView={(id) => navigate(`/jobs/${id}`)}
                onDelete={(id) => deleteJobMutation.mutate(id)}
                onAbandon={(id) => abandonJobMutation.mutate(id)}
              />
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={page}
            totalPages={Math.ceil((data?.total || 0) / 50)}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
```

### 2.5 Migration Strategy

**Incremental Migration:**
1. Set up React app alongside existing Flask templates
2. Create `/app` route that serves React SPA
3. Gradually migrate pages one-by-one
4. Use Flask only for API endpoints
5. Eventually serve React build from Flask static folder

**Vite Configuration:**
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // Proxy API calls to FastAPI during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/realtime/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: '../arm/ui/static/dist',
    emptyOutDir: true,
  },
});
```

---

## Phase 3: Additional Enhancements

### 3.1 Multi-User Support
- JWT authentication
- User roles (admin, viewer)
- Per-user settings

### 3.2 Enhanced Notifications
- Browser push notifications (Web Push API)
- Apprise integration UI
- Notification preferences

### 3.3 Analytics Dashboard
- Rip success rate over time
- Average rip time by disc type
- Storage usage charts
- Drive health monitoring

### 3.4 Mobile PWA
- Service worker for offline support
- App manifest
- Install prompt
- Mobile-optimized UI

### 3.5 Advanced Features
- Batch operations (delete multiple, retry failed)
- Export job history (CSV, JSON)
- Custom metadata scraping rules
- MakeMKV profile editor UI
- HandBrake preset manager

---

## Implementation Checklist

### Phase 1: Performance & Scalability

#### Backend (FastAPI Migration)
- [ ] Set up FastAPI project structure
- [ ] Migrate configuration management (environment variables)
- [ ] Implement async database layer (SQLAlchemy 2.0)
- [ ] Add database indexes to Job model
- [ ] Create Pydantic schemas
- [ ] Migrate authentication (JWT tokens)
- [ ] Implement job management endpoints
- [ ] Implement settings endpoints
- [ ] Implement log viewing endpoints
- [ ] Implement drive management endpoints
- [ ] Implement notification endpoints

#### Real-Time Updates
- [ ] Set up WebSocket endpoint
- [ ] Implement connection manager
- [ ] Create background job progress monitor
- [ ] Integrate log parsers (MakeMKV, HandBrake, abcde)
- [ ] Test WebSocket reconnection logic
- [ ] Alternative: Implement SSE endpoint
- [ ] Update frontend to use WebSocket/SSE

#### Search & Filtering
- [ ] Implement pagination endpoint
- [ ] Add filtering by status, type, date
- [ ] Implement text search
- [ ] Set up SQLite FTS5 virtual table
- [ ] Add advanced search endpoint
- [ ] Create database migration script for indexes
- [ ] Test with 3000+ job database

#### Testing
- [ ] Unit tests for services
- [ ] API endpoint tests
- [ ] WebSocket connection tests
- [ ] Load testing with many concurrent jobs
- [ ] Database query performance testing

#### Deployment
- [ ] Update Docker configuration for Uvicorn
- [ ] Environment variable documentation
- [ ] Migration guide from Flask to FastAPI
- [ ] Backup procedure before migration

### Phase 2: Frontend Modernization

#### Setup
- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure Tailwind CSS
- [ ] Set up shadcn/ui components
- [ ] Configure React Router
- [ ] Set up TanStack Query
- [ ] Configure Zustand store

#### Components
- [ ] Layout components (Header, Sidebar, Footer)
- [ ] Dark mode toggle
- [ ] Job card component
- [ ] Job details component
- [ ] Progress bar component
- [ ] Search bar component
- [ ] Filters component
- [ ] Pagination component
- [ ] Loading states
- [ ] Error boundaries

#### Pages
- [ ] Job list page
- [ ] Job detail page
- [ ] Active rips page
- [ ] History page
- [ ] Settings page
- [ ] Logs page
- [ ] Database view page

#### Hooks & API
- [ ] useJobs hook
- [ ] useJobDetails hook
- [ ] useRealTimeJobs hook
- [ ] API client setup
- [ ] WebSocket manager
- [ ] Error handling

#### Build & Deploy
- [ ] Production build optimization
- [ ] Code splitting
- [ ] Bundle analysis
- [ ] Integrate with Flask static serving
- [ ] Update navigation

### Phase 3: Additional Features
- [ ] Multi-user authentication
- [ ] Push notifications
- [ ] Analytics dashboard
- [ ] PWA setup
- [ ] Batch operations

---

## Testing Strategy

### Unit Tests
- FastAPI endpoints (pytest)
- Service layer logic
- Database queries
- Log parsers

### Integration Tests
- Full API workflow tests
- Database migration tests
- WebSocket message flow

### E2E Tests
- Playwright/Cypress for frontend
- Critical user flows
- Mobile responsive testing

### Performance Tests
- Load testing with k6 or Locust
- Database query optimization
- WebSocket concurrent connections

---

## Deployment Guide

### Development Environment
```bash
# Backend
cd arm/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (during Phase 2)
cd frontend
npm install
npm run dev  # Runs on port 3000, proxies to :8000
```

### Production Deployment
```bash
# Build frontend
cd frontend
npm run build  # Outputs to arm/ui/static/dist

# Run FastAPI with Uvicorn
cd arm
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Docker
docker build -t arm-web .
docker run -p 8000:8000 arm-web
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY arm/ ./arm/

# Expose port
EXPOSE 8000

# Run with Uvicorn
CMD ["uvicorn", "arm.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Migration Timeline Estimate

**Phase 1: Performance & Scalability**
- Weeks 1-2: FastAPI setup, configuration, database optimization
- Weeks 3-4: RESTful API implementation
- Weeks 5-6: Real-time updates (WebSocket/SSE)
- Weeks 7-8: Advanced search, testing, deployment

**Phase 2: Frontend Modernization**
- Weeks 9-10: React setup, core components, layout
- Weeks 11-12: Job management pages
- Weeks 13-14: Settings, logs, other pages
- Weeks 15-16: Polish, testing, migration completion

**Phase 3: Additional Features**
- Ongoing after Phase 2

---

## Success Metrics

### Performance
- [ ] Initial page load < 2 seconds
- [ ] Job list loads 1000+ items smoothly
- [ ] Real-time updates < 500ms latency
- [ ] Database queries < 100ms (95th percentile)
- [ ] Search results < 200ms

### User Experience
- [ ] Lighthouse score > 90
- [ ] Mobile responsive (all screen sizes)
- [ ] Dark mode works perfectly
- [ ] No layout shift (CLS < 0.1)
- [ ] Accessibility score > 90

### Code Quality
- [ ] Test coverage > 80%
- [ ] TypeScript strict mode enabled
- [ ] No console errors
- [ ] Bundle size < 500KB (gzipped)
- [ ] Clean separation of concerns

---

## Notes & Considerations

### Backward Compatibility
- Keep Flask UI available during migration
- Provide fallback for non-WebSocket browsers
- Support old API endpoints temporarily

### Security
- [ ] Fix hardcoded secrets (CRITICAL)
- [ ] Implement CSRF protection
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] Sanitize user content
- [ ] Secure WebSocket connections

### Database
- SQLite works well for single-user
- Consider PostgreSQL for multi-user future
- Regular backups during migration
- Test with large datasets (10,000+ jobs)

### Browser Support
- Modern browsers only (last 2 versions)
- Progressive enhancement for older browsers
- Polyfills if needed

---

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query)

### Tools
- [Vite](https://vitejs.dev/)
- [Playwright](https://playwright.dev/) (E2E testing)
- [Vitest](https://vitest.dev/) (Unit testing)

---

## Questions & Decisions

1. **Do we want to support multiple concurrent users?**
   - Affects authentication design
   - May require PostgreSQL instead of SQLite

2. **Should we keep polling as fallback for WebSocket?**
   - Better compatibility
   - Graceful degradation

3. **Mobile app in the future?**
   - Affects API design
   - Consider React Native or PWA only

4. **Cloud deployment plans?**
   - Docker, kubernetes, cloud-native features

5. **i18n (internationalization) support?**
   - Multiple language support
   - Affects text management

---

**Next Steps:** Begin Phase 1 implementation with FastAPI setup and database optimization.
