"""
Pydantic Schemas for Job API
Defines request/response models for job endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enum (matches JobState from models)"""
    SUCCESS = "success"
    FAILURE = "fail"
    WAITING = "waiting"
    ACTIVE = "active"
    RIPPING = "ripping"
    INFO = "info"
    TRANSCODING = "transcoding"
    WAITING_TRANSCODE = "waiting_transcode"


class VideoType(str, Enum):
    """Video type enum"""
    MOVIE = "movie"
    TV = "series"
    UNKNOWN = "unknown"


class DiscType(str, Enum):
    """Disc type enum"""
    DVD = "dvd"
    BLURAY = "bluray"
    DATA = "data"
    MUSIC = "music"
    UNKNOWN = "unknown"


# ============================================================================
# Base Schemas
# ============================================================================

class JobBase(BaseModel):
    """Base job fields (shared across create/update)"""
    title: Optional[str] = None
    year: Optional[str] = Field(None, max_length=4)
    video_type: Optional[str] = None
    poster_url: Optional[str] = None
    imdb_id: Optional[str] = Field(None, max_length=15)
    hasnicetitle: Optional[bool] = None


# ============================================================================
# Request Schemas
# ============================================================================

class JobCreate(JobBase):
    """Schema for creating a new job"""
    crc_id: str = Field(..., max_length=63, description="Unique CRC identifier for disc")
    label: str = Field(..., max_length=256, description="Disc label")
    devpath: str = Field(..., max_length=15, description="Device path (e.g., /dev/sr0)")
    disctype: Optional[DiscType] = DiscType.UNKNOWN


class JobUpdate(JobBase):
    """Schema for updating an existing job"""
    status: Optional[JobStatus] = None
    stage: Optional[str] = Field(None, max_length=63)
    title_manual: Optional[str] = Field(None, max_length=256)
    year_manual: Optional[str] = Field(None, max_length=4)
    video_type_manual: Optional[str] = Field(None, max_length=20)
    imdb_id_manual: Optional[str] = Field(None, max_length=15)
    poster_url_manual: Optional[str] = Field(None, max_length=256)


class JobFilter(BaseModel):
    """Schema for filtering jobs"""
    status: Optional[str] = None
    video_type: Optional[str] = None
    disctype: Optional[str] = None
    search: Optional[str] = None
    hasnicetitle: Optional[bool] = None


class JobSearchParams(BaseModel):
    """Schema for advanced job search"""
    query: Optional[str] = Field(None, description="Text search query")
    statuses: Optional[List[str]] = Field(None, description="Filter by multiple statuses")
    video_types: Optional[List[str]] = Field(None, description="Filter by video types")
    disctypes: Optional[List[str]] = Field(None, description="Filter by disc types")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    min_year: Optional[int] = Field(None, ge=1900, le=2100, description="Minimum release year")
    max_year: Optional[int] = Field(None, ge=1900, le=2100, description="Maximum release year")
    has_errors: Optional[bool] = Field(None, description="Filter jobs with errors")


# ============================================================================
# Response Schemas
# ============================================================================

class JobResponse(JobBase):
    """Schema for job responses (includes all fields)"""
    job_id: int
    arm_version: Optional[str] = None
    crc_id: Optional[str] = None
    logfile: Optional[str] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    job_length: Optional[str] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    no_of_titles: Optional[int] = None

    # Title fields (auto/manual)
    title_auto: Optional[str] = None
    title_manual: Optional[str] = None

    # Year fields (auto/manual)
    year_auto: Optional[str] = None
    year_manual: Optional[str] = None

    # Video type fields (auto/manual)
    video_type_auto: Optional[str] = None
    video_type_manual: Optional[str] = None

    # IMDB fields (auto/manual)
    imdb_id_auto: Optional[str] = None
    imdb_id_manual: Optional[str] = None

    # Poster URL fields (auto/manual)
    poster_url_auto: Optional[str] = None
    poster_url_manual: Optional[str] = None

    # Device info
    devpath: Optional[str] = None
    mountpoint: Optional[str] = None

    # Disc info
    disctype: Optional[str] = None
    label: Optional[str] = None
    path: Optional[str] = None

    # Flags
    ejected: Optional[bool] = None
    updated: Optional[bool] = None
    is_iso: Optional[bool] = None
    manual_start: Optional[bool] = None
    manual_mode: Optional[bool] = None

    # Process info
    pid: Optional[int] = None
    pid_hash: Optional[int] = None

    # Errors
    errors: Optional[str] = None

    # Progress (computed field)
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")

    model_config = ConfigDict(from_attributes=True)


class JobSummary(BaseModel):
    """Minimal job information for lists"""
    job_id: int
    title: Optional[str] = None
    year: Optional[str] = None
    status: Optional[str] = None
    video_type: Optional[str] = None
    disctype: Optional[str] = None
    poster_url: Optional[str] = None
    start_time: Optional[datetime] = None
    progress: Optional[float] = None
    crc_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Response for job list with pagination"""
    jobs: List[JobSummary]
    total: int
    skip: int = 0
    limit: int = 50
    has_more: bool = False

    @property
    def current_page(self) -> int:
        """Calculate current page number"""
        return (self.skip // self.limit) + 1

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages"""
        return (self.total + self.limit - 1) // self.limit


# ============================================================================
# Action Schemas
# ============================================================================

class JobAbandonRequest(BaseModel):
    """Request to abandon/kill a running job"""
    reason: Optional[str] = Field(None, description="Reason for abandoning job")


class JobDeleteRequest(BaseModel):
    """Request to delete a job"""
    delete_files: bool = Field(False, description="Also delete physical files")


class JobTitleSearchRequest(BaseModel):
    """Request to search for title metadata"""
    query: str = Field(..., min_length=1, description="Title to search for")
    year: Optional[str] = Field(None, max_length=4, description="Release year")
    video_type: Optional[VideoType] = Field(None, description="Movie or TV series")


class JobTitleUpdateRequest(BaseModel):
    """Request to update job with metadata from search"""
    title: str = Field(..., max_length=256)
    year: Optional[str] = Field(None, max_length=4)
    video_type: Optional[str] = Field(None, max_length=20)
    poster_url: Optional[str] = Field(None, max_length=256)
    imdb_id: Optional[str] = Field(None, max_length=15)


# ============================================================================
# Statistics Schemas
# ============================================================================

class JobStatistics(BaseModel):
    """Job statistics"""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    active_jobs: int
    success_rate: float = Field(..., ge=0, le=100)
    average_job_length: Optional[str] = None
    total_discs_processed: int

    # By disc type
    dvd_count: int
    bluray_count: int
    music_count: int

    # By video type
    movie_count: int
    tv_count: int


# ============================================================================
# Progress Update Schema (for WebSocket)
# ============================================================================

class JobProgressUpdate(BaseModel):
    """Real-time progress update"""
    job_id: int
    progress: float = Field(..., ge=0, le=100)
    stage: Optional[str] = None
    status: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
