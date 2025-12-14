#!/usr/bin/env python3
"""
Simple FastAPI component test
Tests that our new API components work independently
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("FastAPI Component Test")
print("=" * 60)

# Test imports directly (bypass arm package init)
print("\n[1/5] Testing imports...")
try:
    # Import directly from modules
    import importlib.util

    # Load config module
    spec = importlib.util.spec_from_file_location(
        "api_config",
        "arm/api/config.py"
    )
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    settings = config_module.settings
    print(f"   [OK] Config loaded")
    print(f"   - Secret key length: {len(settings.SECRET_KEY)}")
    print(f"   - API prefix: {settings.API_V1_PREFIX}")
    print(f"   - Port: {settings.PORT}")

except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[2/5] Testing Pydantic schemas...")
try:
    spec = importlib.util.spec_from_file_location(
        "job_schema",
        "arm/api/schemas/job.py"
    )
    job_schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job_schema)

    # Create a test job response
    job = job_schema.JobResponse(
        job_id=1,
        title="Test Movie",
        year="2024",
        status="success"
    )
    print(f"   [OK] Job schema works")
    print(f"   - Job ID: {job.job_id}")
    print(f"   - Title: {job.title}")

except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()

print("\n[3/5] Checking database module...")
try:
    spec = importlib.util.spec_from_file_location(
        "api_database",
        "arm/api/database.py"
    )
    db_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_module)

    print(f"   [OK] Database module structure valid")

except Exception as e:
    print(f"   [FAIL] {e}")

print("\n[4/5] Checking dependencies...")
try:
    spec = importlib.util.spec_from_file_location(
        "api_deps",
        "arm/api/dependencies.py"
    )
    deps_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deps_module)

    print(f"   [OK] Dependencies module valid")

except Exception as e:
    print(f"   [FAIL] {e}")

print("\n[5/5] Checking main app structure...")
try:
    # Check if main.py exists and has basic structure
    with open("arm/api/main.py", "r") as f:
        content = f.read()
        checks = [
            ("FastAPI app", "app = FastAPI(" in content),
            ("Health endpoint", "def health_check" in content),
            ("Lifespan", "async def lifespan" in content),
            ("CORS middleware", "CORSMiddleware" in content),
        ]

        for check_name, result in checks:
            status = "[OK]" if result else "[MISSING]"
            print(f"   {status} {check_name}")

except Exception as e:
    print(f"   [FAIL] {e}")

print("\n" + "=" * 60)
print("Component structure test complete!")
print("=" * 60)
print("\nTo start the server:")
print("  uvicorn arm.api.main:app --reload --port 8000")
print("\nThen visit:")
print("  http://localhost:8000/api/docs")
