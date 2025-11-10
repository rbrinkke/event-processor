"""
Import Validation Test
Test of alle modules correct importeren zonder runtime errors
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

print("🔍 Testing imports...")
errors = []

# Test 1: Models
try:
    from app.models import OutboxEvent, DebeziumPayload, EventStatus, ProcessingResult
    print("✓ app.models")
except Exception as e:
    errors.append(f"✗ app.models: {e}")
    print(f"✗ app.models: {e}")

# Test 2: Config (requires .env maar heeft defaults)
try:
    from app.config import settings, Settings
    print("✓ app.config")
except Exception as e:
    errors.append(f"✗ app.config: {e}")
    print(f"✗ app.config: {e}")

# Test 3: Database module
try:
    from app.database.mongodb import MongoDBManager, mongodb
    print("✓ app.database.mongodb")
except Exception as e:
    errors.append(f"✗ app.database.mongodb: {e}")
    print(f"✗ app.database.mongodb: {e}")

# Test 4: Base handler
try:
    from app.handlers.base import BaseEventHandler
    print("✓ app.handlers.base")
except Exception as e:
    errors.append(f"✗ app.handlers.base: {e}")
    print(f"✗ app.handlers.base: {e}")

# Test 5: User handlers
try:
    from app.handlers.user_handlers import UserCreatedHandler, UserUpdatedHandler, UserStatisticsHandler
    print("✓ app.handlers.user_handlers")
except Exception as e:
    errors.append(f"✗ app.handlers.user_handlers: {e}")
    print(f"✗ app.handlers.user_handlers: {e}")

# Test 6: Activity handlers
try:
    from app.handlers.activity_handlers import ActivityCreatedHandler, ParticipantJoinedHandler, ActivityUpdatedHandler
    print("✓ app.handlers.activity_handlers")
except Exception as e:
    errors.append(f"✗ app.handlers.activity_handlers: {e}")
    print(f"✗ app.handlers.activity_handlers: {e}")

# Test 7: Registry
try:
    from app.registry import HandlerRegistry, handler_registry
    print("✓ app.registry")
except Exception as e:
    errors.append(f"✗ app.registry: {e}")
    print(f"✗ app.registry: {e}")

# Test 8: Consumer
try:
    from app.consumer import EventConsumer
    print("✓ app.consumer")
except Exception as e:
    errors.append(f"✗ app.consumer: {e}")
    print(f"✗ app.consumer: {e}")

# Test 9: Main application
try:
    from app.main import Application
    print("✓ app.main")
except Exception as e:
    errors.append(f"✗ app.main: {e}")
    print(f"✗ app.main: {e}")

# Summary
print("\n" + "="*50)
if errors:
    print(f"❌ Import test FAILED: {len(errors)} errors")
    for error in errors:
        print(f"  {error}")
    sys.exit(1)
else:
    print("✅ All imports successful!")
    print("="*50)
    sys.exit(0)
