#!/usr/bin/env python3
"""
FastAPI Server Startup Script
Starts the FastAPI backend independently of the Flask UI
"""
import sys
import os

# Set working directory
os.chdir(os.path.dirname(__file__))

# Create a minimal mock for arm.config to allow import
print("Setting up ARM config mock...")

# Create mock config module
import types
arm = types.ModuleType('arm')
arm_config_module = types.ModuleType('arm.config')
arm_config_config = types.ModuleType('arm.config.config')

# Mock the config
arm_config_config.arm_config = {
    'DBFILE': 'arm.db',
    'LOGLEVEL': 'INFO',
    'DISABLE_LOGIN': False,
    'LOGPATH': 'logs',
    'RAWPATH': 'raw',
    'COMPLETED_PATH': 'completed',
}

# Install mocks
sys.modules['arm'] = arm
sys.modules['arm.config'] = arm_config_module
sys.modules['arm.config.config'] = arm_config_config

# Prevent arm from trying to import its submodules
arm.__path__ = []
arm_config_module.config = arm_config_config

print("ARM config mocked successfully")

# Now we can import FastAPI app
print("Loading FastAPI application...")
from arm.api.main import app
from arm.api.config import settings

print("=" * 60)
print("ARM FastAPI Backend Server")
print("=" * 60)
print(f"Version: {settings.VERSION}")
print(f"Host: {settings.HOST}")
print(f"Port: {settings.PORT}")
print(f"Database: {settings.get_database_url()}")
print(f"Login Disabled: {settings.is_login_disabled()}")
print("=" * 60)
print("\nStarting server...")
print(f"API Documentation: http://{settings.HOST}:{settings.PORT}{settings.API_V1_PREFIX}/docs")
print(f"Health Check: http://{settings.HOST}:{settings.PORT}{settings.API_V1_PREFIX}/health")
print("=" * 60)
print("\nPress Ctrl+C to stop the server\n")

# Start uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.get_log_level().lower(),
    )
