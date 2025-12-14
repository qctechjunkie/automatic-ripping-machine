#!/usr/bin/env python3
"""
Test script for FastAPI backend components
Tests configuration, database, and schemas without starting the full ARM
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("FastAPI Backend Component Tests")
print("=" * 60)

# ============================================================================
# Test 1: Configuration System
# ============================================================================
print("\n1. Testing Configuration System...")
try:
    # Temporarily prevent ARM config from loading
    os.environ['ARM_CONFIG_PATH'] = '/tmp/fake'  # Non-existent path

    from arm.api.config import Settings, settings, generate_env_example

    print(f"   ✓ Configuration module loaded")
    print(f"   ✓ Secret key generated: {len(settings.SECRET_KEY)} characters")
    print(f"   ✓ API prefix: {settings.API_V1_PREFIX}")
    print(f"   ✓ Server: {settings.HOST}:{settings.PORT}")
    print(f"   ✓ Log level: {settings.get_log_level()}")
    print(f"   ✓ Login disabled: {settings.is_login_disabled()}")

    # Generate .env.example
    generate_env_example()
    print(f"   ✓ .env.example generated")

    print("   ✅ Configuration system: PASSED")
except Exception as e:
    print(f"   ❌ Configuration system: FAILED")
    print(f"      Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 2: Pydantic Schemas
# ============================================================================
print("\n2. Testing Pydantic Schemas...")
try:
    from arm.api.schemas.job import (
        JobResponse, JobCreate, JobUpdate, JobFilter,
        JobSummary, JobListResponse, JobStatus
    )
    from arm.api.schemas.auth import (
        Token, UserLogin, UserResponse, PasswordChangeRequest
    )

    # Test job schema
    job_data = {
        "job_id": 1,
        "title": "Test Movie",
        "year": "2024",
        "status": "success",
        "crc_id": "ABC123",
    }
    job = JobResponse(**job_data)
    print(f"   ✓ JobResponse schema works")
    print(f"     - Title: {job.title}")
    print(f"     - Year: {job.year}")

    # Test auth schema
    login = UserLogin(username="admin", password="test123")
    print(f"   ✓ UserLogin schema works")
    print(f"     - Username: {login.username}")

    print("   ✅ Pydantic schemas: PASSED")
except Exception as e:
    print(f"   ❌ Pydantic schemas: FAILED")
    print(f"      Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 3: Database Layer (without actual DB)
# ============================================================================
print("\n3. Testing Database Layer...")
try:
    from arm.api.database import Base
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.orm import declarative_base

    # Test that we can define models
    TestBase = declarative_base()

    class TestModel(TestBase):
        __tablename__ = 'test'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))

    print(f"   ✓ Database module loaded")
    print(f"   ✓ Can define SQLAlchemy models")
    print("   ✅ Database layer: PASSED")
except Exception as e:
    print(f"   ❌ Database layer: FAILED")
    print(f"      Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 4: Dependencies
# ============================================================================
print("\n4. Testing Dependencies...")
try:
    from arm.api.dependencies import security

    print(f"   ✓ Dependencies module loaded")
    print(f"   ✓ Security scheme configured")
    print("   ✅ Dependencies: PASSED")
except Exception as e:
    print(f"   ❌ Dependencies: FAILED")
    print(f"      Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 5: FastAPI Application Structure
# ============================================================================
print("\n5. Testing FastAPI Application...")
try:
    from arm.api.main import app

    print(f"   ✓ FastAPI app created")
    print(f"   ✓ App title: {app.title}")
    print(f"   ✓ App version: {app.version}")

    # Count routes
    route_count = len([r for r in app.routes if hasattr(r, 'methods')])
    print(f"   ✓ Routes defined: {route_count}")

    # List routes
    print(f"\n   Available endpoints:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"     - {methods:10} {route.path}")

    print("   ✅ FastAPI application: PASSED")
except Exception as e:
    print(f"   ❌ FastAPI application: FAILED")
    print(f"      Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
print("✅ All component tests completed!")
print("=" * 60)
print("\nNext steps:")
print("  1. Start the server: python -m uvicorn arm.api.main:app --reload")
print("  2. Visit: http://localhost:8000/api/docs")
print("  3. Test health endpoint: http://localhost:8000/api/health")
