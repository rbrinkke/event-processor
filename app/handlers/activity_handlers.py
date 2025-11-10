"""
Activity Event Handlers
Handlers voor activity-gerelateerde events
"""

from datetime import datetime

from app.handlers.base import BaseEventHandler
from app.models import OutboxEvent
from app.database.mongodb import mongodb


class ActivityCreatedHandler(BaseEventHandler):
    """
    Handler voor ActivityCreated events

    Schrijft activity document naar MongoDB
    """

    @property
    def event_type(self) -> str:
        return "ActivityCreated"

    async def handle(self, event: OutboxEvent) -> None:
        """Create activity document"""
        self.log_event(event, "processing_activity_created")

        payload = event.payload

        # Build activity document
        activity_doc = {
            "_id": str(event.aggregate_id),
            "title": payload.get("title"),
            "description": payload.get("description"),
            "creator_id": payload.get("creator_user_id"),
            "type": payload.get("activity_type"),
            "location": {
                "name": payload.get("location_name"),
                "address": payload.get("location_address"),
                "coordinates": payload.get("coordinates"),  # GeoJSON
            },
            "schedule": {
                "start_date": payload.get("start_date"),
                "end_date": payload.get("end_date"),
                "timezone": payload.get("timezone"),
            },
            "participants": {
                "current_count": 0,
                "max_count": payload.get("max_participants"),
                "list": [],
            },
            "status": "active",
            "metadata": {
                "created_at": event.created_at,
                "updated_at": datetime.utcnow(),
                "source_event_id": str(event.event_id),
            },
            # IDOR prevention - wie mag dit zien?
            "allowed_users": [payload.get("creator_user_id")],
        }

        # Insert into MongoDB
        activities_collection = mongodb.collection("activities")
        await activities_collection.insert_one(activity_doc)

        self.log_event(
            event,
            "activity_created_success",
            activity_id=str(event.aggregate_id),
            title=payload.get("title"),
        )


class ParticipantJoinedHandler(BaseEventHandler):
    """
    Handler voor ParticipantJoined events

    Update activity document met nieuwe participant
    """

    @property
    def event_type(self) -> str:
        return "ParticipantJoined"

    async def handle(self, event: OutboxEvent) -> None:
        """Add participant to activity"""
        self.log_event(event, "processing_participant_joined")

        payload = event.payload
        activity_id = str(event.aggregate_id)
        user_id = payload.get("user_id")

        # Update activity document
        activities_collection = mongodb.collection("activities")

        result = await activities_collection.update_one(
            {"_id": activity_id},
            {
                "$addToSet": {
                    "participants.list": {
                        "user_id": user_id,
                        "joined_at": event.created_at,
                        "status": "confirmed",
                    },
                    "allowed_users": user_id,  # IDOR: participant kan nu deze activity zien
                },
                "$inc": {"participants.current_count": 1},
                "$set": {
                    "metadata.updated_at": datetime.utcnow(),
                    "metadata.last_event_id": str(event.event_id),
                },
            },
        )

        if result.matched_count == 0:
            self.log_error(event, Exception(f"Activity not found: {activity_id}"))
            raise ValueError(f"Activity not found: {activity_id}")

        self.log_event(
            event,
            "participant_joined_success",
            activity_id=activity_id,
            user_id=user_id,
        )


class ActivityUpdatedHandler(BaseEventHandler):
    """
    Handler voor ActivityUpdated events
    """

    @property
    def event_type(self) -> str:
        return "ActivityUpdated"

    async def handle(self, event: OutboxEvent) -> None:
        """Update activity document"""
        self.log_event(event, "processing_activity_updated")

        payload = event.payload
        activity_id = str(event.aggregate_id)

        # Build update document
        update_fields = {}

        if "title" in payload:
            update_fields["title"] = payload["title"]
        if "description" in payload:
            update_fields["description"] = payload["description"]
        if "status" in payload:
            update_fields["status"] = payload["status"]

        # Nested updates
        if "location_name" in payload:
            update_fields["location.name"] = payload["location_name"]
        if "location_address" in payload:
            update_fields["location.address"] = payload["location_address"]

        # Metadata
        update_fields["metadata.updated_at"] = datetime.utcnow()
        update_fields["metadata.last_event_id"] = str(event.event_id)

        # Update MongoDB
        activities_collection = mongodb.collection("activities")
        result = await activities_collection.update_one(
            {"_id": activity_id}, {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise ValueError(f"Activity not found: {activity_id}")

        self.log_event(event, "activity_updated_success", activity_id=activity_id)
