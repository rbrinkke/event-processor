"""
User Event Handlers
Handlers voor user-gerelateerde events
"""

from datetime import datetime

from app.handlers.base import BaseEventHandler
from app.models import OutboxEvent
from app.database.mongodb import mongodb


class UserCreatedHandler(BaseEventHandler):
    """
    Handler voor UserCreated events

    Schrijft het user document naar de 'users' collectie in MongoDB
    """

    @property
    def event_type(self) -> str:
        return "UserCreated"

    async def handle(self, event: OutboxEvent) -> None:
        """
        Create user document in MongoDB

        Event payload structure:
        {
            "user_id": "uuid",
            "email": "user@example.com",
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": "2024-01-01T12:00:00Z"
        }
        """
        self.log_event(event, "processing_user_created")

        payload = event.payload

        # Build MongoDB document
        user_doc = {
            "_id": str(event.aggregate_id),  # Use aggregate_id as _id
            "email": payload.get("email"),
            "username": payload.get("username"),
            "name": f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip(),
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "profile": {
                "bio": payload.get("bio"),
                "avatar_url": payload.get("avatar_url"),
            },
            "metadata": {
                "created_at": event.created_at,
                "updated_at": datetime.utcnow(),
                "source_event_id": str(event.event_id),
            },
            # Voor IDOR prevention
            "allowed_users": [str(event.aggregate_id)],
        }

        # Insert into MongoDB
        users_collection = mongodb.collection("users")
        await users_collection.insert_one(user_doc)

        self.log_event(
            event,
            "user_created_success",
            user_id=str(event.aggregate_id),
            username=payload.get("username"),
        )


class UserUpdatedHandler(BaseEventHandler):
    """
    Handler voor UserUpdated events

    Update user document in MongoDB
    """

    @property
    def event_type(self) -> str:
        return "UserUpdated"

    async def handle(self, event: OutboxEvent) -> None:
        """Update user document"""
        self.log_event(event, "processing_user_updated")

        payload = event.payload
        user_id = str(event.aggregate_id)

        # Build update document
        update_fields = {}

        if "email" in payload:
            update_fields["email"] = payload["email"]
        if "username" in payload:
            update_fields["username"] = payload["username"]
        if "first_name" in payload or "last_name" in payload:
            first_name = payload.get("first_name", "")
            last_name = payload.get("last_name", "")
            update_fields["name"] = f"{first_name} {last_name}".strip()
            update_fields["first_name"] = first_name
            update_fields["last_name"] = last_name

        if "bio" in payload:
            update_fields["profile.bio"] = payload["bio"]
        if "avatar_url" in payload:
            update_fields["profile.avatar_url"] = payload["avatar_url"]

        # Always update metadata
        update_fields["metadata.updated_at"] = datetime.utcnow()
        update_fields["metadata.last_event_id"] = str(event.event_id)

        # Update MongoDB
        users_collection = mongodb.collection("users")
        result = await users_collection.update_one(
            {"_id": user_id}, {"$set": update_fields}
        )

        if result.matched_count == 0:
            self.log_error(event, Exception(f"User not found: {user_id}"))
            raise ValueError(f"User not found: {user_id}")

        self.log_event(
            event,
            "user_updated_success",
            user_id=user_id,
            modified_count=result.modified_count,
        )


class UserStatisticsHandler(BaseEventHandler):
    """
    Handler voor UserCreated events

    Update global statistics (voorbeeld van multiple handlers voor één event type)
    """

    @property
    def event_type(self) -> str:
        return "UserCreated"

    async def handle(self, event: OutboxEvent) -> None:
        """Increment global user count"""
        self.log_event(event, "updating_user_statistics")

        stats_collection = mongodb.collection("statistics")

        await stats_collection.update_one(
            {"_id": "global_stats"},
            {"$inc": {"total_users": 1}, "$set": {"last_updated": datetime.utcnow()}},
            upsert=True,
        )

        self.log_event(event, "user_statistics_updated")
