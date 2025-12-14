"""
FastAPI Configuration Management
Fixes hardcoded secrets issue from Flask version (arm/ui/__init__.py:56)
"""
import secrets
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    This replaces the hardcoded secrets from the Flask version:
    - SECRET_KEY was "Big secret key" (arm/ui/__init__.py:56)
    - WERKZEUG_DEBUG_PIN was "12345" (arm/ui/__init__.py:61)

    Now properly uses environment variables or generates secure random values.
    """

    # =========================================================================
    # Security Settings
    # =========================================================================
    SECRET_KEY: str = secrets.token_urlsafe(32)
    """Secret key for JWT signing. Auto-generates secure random key if not provided."""

    ALGORITHM: str = "HS256"
    """JWT signing algorithm"""

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    """JWT token expiration time in minutes"""

    # =========================================================================
    # Database Settings
    # =========================================================================
    DATABASE_URL: Optional[str] = None
    """
    Database connection URL. If not provided, uses ARM_CONFIG_PATH to find arm.yaml
    and constructs SQLite URL from DBFILE setting.
    Example: sqlite+aiosqlite:///path/to/arm.db
    """

    # =========================================================================
    # CORS Settings
    # =========================================================================
    ALLOWED_ORIGINS: List[str] = ["*"]
    """
    CORS allowed origins. Default allows all.
    For production, set to specific domains:
    ALLOWED_ORIGINS=["http://localhost:3000","https://arm.example.com"]
    """

    # =========================================================================
    # ARM Configuration Paths (from existing ARM setup)
    # =========================================================================
    ARM_CONFIG_PATH: str = "/etc/arm/config"
    """Path to ARM configuration directory"""

    ARM_CONFIG_FILE: str = "arm.yaml"
    """ARM configuration file name"""

    # =========================================================================
    # Feature Flags
    # =========================================================================
    DISABLE_LOGIN: bool = False
    """Disable authentication requirement (matches Flask LOGIN_DISABLED)"""

    # =========================================================================
    # Server Settings
    # =========================================================================
    HOST: str = "0.0.0.0"
    """Server host address"""

    PORT: int = 8000
    """Server port"""

    WORKERS: int = 4
    """Number of Uvicorn worker processes"""

    RELOAD: bool = False
    """Enable auto-reload on code changes (development only)"""

    LOG_LEVEL: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"""

    # =========================================================================
    # WebSocket Settings
    # =========================================================================
    WS_HEARTBEAT_INTERVAL: int = 30
    """WebSocket heartbeat interval in seconds"""

    WS_MESSAGE_QUEUE_SIZE: int = 100
    """Maximum WebSocket message queue size"""

    # =========================================================================
    # API Settings
    # =========================================================================
    API_V1_PREFIX: str = "/api"
    """API route prefix"""

    PROJECT_NAME: str = "Automatic Ripping Machine API"
    """API project name"""

    VERSION: str = "3.0.0"
    """API version"""

    DESCRIPTION: str = "REST API for ARM disc ripping automation"
    """API description"""

    # =========================================================================
    # Pydantic Settings Configuration
    # =========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """
        Get database URL. If DATABASE_URL is not set, load from ARM config.

        Returns:
            str: Database connection URL
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # Load from ARM config (same as Flask version)
        try:
            import arm.config.config as cfg
            dbfile = cfg.arm_config.get('DBFILE', 'arm.db')
            # Convert to async SQLite URL
            return f"sqlite+aiosqlite:///{dbfile}"
        except Exception as e:
            # Fallback to default
            print(f"Warning: Could not load ARM config: {e}")
            return "sqlite+aiosqlite:///arm.db"

    def get_log_level(self) -> str:
        """
        Get log level. If not set, try to load from ARM config.

        Returns:
            str: Log level
        """
        if self.LOG_LEVEL != "INFO":
            return self.LOG_LEVEL

        # Try to load from ARM config
        try:
            import arm.config.config as cfg
            return cfg.arm_config.get('LOGLEVEL', 'INFO')
        except Exception:
            return "INFO"

    def is_login_disabled(self) -> bool:
        """
        Check if login is disabled. Checks both env var and ARM config.

        Returns:
            bool: True if login should be disabled
        """
        if self.DISABLE_LOGIN:
            return True

        # Check ARM config
        try:
            import arm.config.config as cfg
            return cfg.arm_config.get('DISABLE_LOGIN', False)
        except Exception:
            return False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection function for FastAPI.

    Usage:
        @app.get("/")
        async def root(settings: Settings = Depends(get_settings)):
            return {"secret_configured": bool(settings.SECRET_KEY)}

    Returns:
        Settings: Application settings instance
    """
    return settings


# ============================================================================
# Environment Variable Template (.env.example)
# ============================================================================
ENV_EXAMPLE = """
# Automatic Ripping Machine - FastAPI Environment Configuration
# Copy this file to .env and customize for your environment

# ============================================================================
# Security (REQUIRED for production)
# ============================================================================
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-super-secret-key-here-generate-a-random-one

# ============================================================================
# Database
# ============================================================================
# DATABASE_URL=sqlite+aiosqlite:///path/to/arm.db
# If not set, will use ARM_CONFIG_PATH to find arm.yaml

# ============================================================================
# CORS (Production)
# ============================================================================
# ALLOWED_ORIGINS=["http://localhost:3000","https://arm.example.com"]

# ============================================================================
# Authentication
# ============================================================================
# DISABLE_LOGIN=false
# ACCESS_TOKEN_EXPIRE_MINUTES=60

# ============================================================================
# Server
# ============================================================================
# HOST=0.0.0.0
# PORT=8000
# WORKERS=4
# LOG_LEVEL=INFO

# ============================================================================
# ARM Configuration
# ============================================================================
# ARM_CONFIG_PATH=/etc/arm/config
# ARM_CONFIG_FILE=arm.yaml
"""


def generate_env_example():
    """Generate .env.example file in project root."""
    env_path = Path(__file__).parent.parent.parent / ".env.example"
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(ENV_EXAMPLE)
        print(f"Created .env.example at {env_path}")
    else:
        print(f".env.example already exists at {env_path}")


if __name__ == "__main__":
    # When run directly, print current settings (for debugging)
    print("Current FastAPI Settings:")
    print("=" * 60)
    s = settings
    print(f"Database URL: {s.get_database_url()}")
    print(f"Log Level: {s.get_log_level()}")
    print(f"Login Disabled: {s.is_login_disabled()}")
    print(f"Secret Key Configured: {len(s.SECRET_KEY) > 10}")
    print(f"API Prefix: {s.API_V1_PREFIX}")
    print(f"CORS Origins: {s.ALLOWED_ORIGINS}")
    print(f"Server: {s.HOST}:{s.PORT}")
    print("=" * 60)

    # Generate .env.example
    generate_env_example()
