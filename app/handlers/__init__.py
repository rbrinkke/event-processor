"""
Event Handlers Module
Export alle handlers voor gemakkelijke import
"""

from app.handlers.user_handlers import (
    UserCreatedHandler,
    UserUpdatedHandler,
    UserStatisticsHandler,
)
from app.handlers.activity_handlers import (
    ActivityCreatedHandler,
    ActivityUpdatedHandler,
    ParticipantJoinedHandler,
)

__all__ = [
    "UserCreatedHandler",
    "UserUpdatedHandler",
    "UserStatisticsHandler",
    "ActivityCreatedHandler",
    "ActivityUpdatedHandler",
    "ParticipantJoinedHandler",
]
