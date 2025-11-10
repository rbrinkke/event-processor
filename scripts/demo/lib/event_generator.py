"""
Event Generator - Generate Realistic Test Data
Generates events for PostgreSQL event_outbox table with realistic data using Faker
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
import random

from faker import Faker

# Initialize Faker
fake = Faker()


class EventGenerator:
    """
    Generate realistic test events for the event processor demo

    Features:
    - Realistic user data (names, emails, addresses)
    - Realistic activity data (titles, descriptions, locations)
    - Referential integrity (participants reference real users/activities)
    - Configurable event distribution
    """

    def __init__(self):
        self.generated_user_ids: List[str] = []
        self.generated_activity_ids: List[str] = []

    def generate_user_created_event(self) -> Dict[str, Any]:
        """Generate a UserCreated event with realistic data"""
        user_id = str(uuid.uuid4())
        self.generated_user_ids.append(user_id)

        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(100, 999)}"

        return {
            "event_id": str(uuid.uuid4()),
            "aggregate_id": user_id,
            "aggregate_type": "User",
            "event_type": "UserCreated",
            "payload": {
                "user_id": user_id,
                "email": fake.email(),
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                "phone": fake.phone_number(),
                "address": {
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "state": fake.state(),
                    "zipcode": fake.zipcode(),
                    "country": fake.country_code()
                },
                "preferences": {
                    "notifications_enabled": random.choice([True, False]),
                    "language": random.choice(["en", "nl", "de", "fr"]),
                    "timezone": fake.timezone()
                }
            },
            "status": "pending"
        }

    def generate_user_updated_event(self) -> Dict[str, Any]:
        """Generate a UserUpdated event"""
        if not self.generated_user_ids:
            # If no users yet, create one first
            return self.generate_user_created_event()

        user_id = random.choice(self.generated_user_ids)

        # Random fields to update
        updates = {}
        update_choices = [
            ("phone", fake.phone_number()),
            ("address.city", fake.city()),
            ("preferences.notifications_enabled", random.choice([True, False])),
            ("preferences.timezone", fake.timezone())
        ]

        # Update 1-3 random fields
        for field, value in random.sample(update_choices, k=random.randint(1, 3)):
            updates[field] = value

        return {
            "event_id": str(uuid.uuid4()),
            "aggregate_id": user_id,
            "aggregate_type": "User",
            "event_type": "UserUpdated",
            "payload": {
                "user_id": user_id,
                "updates": updates,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "status": "pending"
        }

    def generate_activity_created_event(self) -> Dict[str, Any]:
        """Generate an ActivityCreated event with realistic activity data"""
        activity_id = str(uuid.uuid4())
        self.generated_activity_ids.append(activity_id)

        # Ensure we have a creator (user)
        if not self.generated_user_ids:
            # Generate a user first
            user_event = self.generate_user_created_event()
            creator_id = user_event["aggregate_id"]
        else:
            creator_id = random.choice(self.generated_user_ids)

        # Activity types and corresponding data
        activity_types = [
            ("Hiking", "Join us for a scenic hike through beautiful trails"),
            ("Cycling", "Group bike ride through the city and countryside"),
            ("Running", "Morning run with a friendly group"),
            ("Yoga", "Relaxing yoga session in the park"),
            ("Coffee Meetup", "Casual coffee and conversation"),
            ("Book Club", "Monthly book discussion and socializing"),
            ("Photography Walk", "Explore the city and practice photography"),
            ("Board Games", "Fun evening of board games and snacks"),
            ("Cooking Class", "Learn to cook delicious meals together"),
            ("Beach Volleyball", "Friendly beach volleyball games")
        ]

        activity_type, description_template = random.choice(activity_types)

        # Schedule: random date within next 30 days
        start_date = fake.date_time_between(start_date="now", end_date="+30d", tzinfo=timezone.utc)

        return {
            "event_id": str(uuid.uuid4()),
            "aggregate_id": activity_id,
            "aggregate_type": "Activity",
            "event_type": "ActivityCreated",
            "payload": {
                "activity_id": activity_id,
                "title": f"{activity_type} - {fake.city()}",
                "description": description_template,
                "activity_type": activity_type,
                "creator_id": creator_id,
                "location": {
                    "name": fake.company(),
                    "address": fake.street_address(),
                    "city": fake.city(),
                    "coordinates": {
                        "lat": float(fake.latitude()),
                        "lng": float(fake.longitude())
                    }
                },
                "schedule": {
                    "start_date": start_date.isoformat(),
                    "duration_minutes": random.choice([30, 60, 90, 120, 180]),
                    "recurring": random.choice([False, False, True])  # 33% recurring
                },
                "participants": {
                    "max_participants": random.randint(5, 50),
                    "current_count": 0,
                    "allowed_users": []
                },
                "requirements": {
                    "skill_level": random.choice(["beginner", "intermediate", "advanced"]),
                    "age_restriction": random.choice([None, 18, 21]),
                    "equipment_needed": random.choice([True, False])
                }
            },
            "status": "pending"
        }

    def generate_activity_updated_event(self) -> Dict[str, Any]:
        """Generate an ActivityUpdated event"""
        if not self.generated_activity_ids:
            # If no activities yet, create one first
            return self.generate_activity_created_event()

        activity_id = random.choice(self.generated_activity_ids)

        return {
            "event_id": str(uuid.uuid4()),
            "aggregate_id": activity_id,
            "aggregate_type": "Activity",
            "event_type": "ActivityUpdated",
            "payload": {
                "activity_id": activity_id,
                "updates": {
                    "max_participants": random.randint(5, 50),
                    "description": fake.sentence(nb_words=10)
                },
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "status": "pending"
        }

    def generate_participant_joined_event(self) -> Dict[str, Any]:
        """Generate a ParticipantJoined event"""
        # Need both users and activities
        if not self.generated_user_ids or not self.generated_activity_ids:
            # Create activity first (which will create user if needed)
            return self.generate_activity_created_event()

        user_id = random.choice(self.generated_user_ids)
        activity_id = random.choice(self.generated_activity_ids)

        return {
            "event_id": str(uuid.uuid4()),
            "aggregate_id": activity_id,
            "aggregate_type": "Activity",
            "event_type": "ParticipantJoined",
            "payload": {
                "activity_id": activity_id,
                "user_id": user_id,
                "joined_at": datetime.now(timezone.utc).isoformat(),
                "status": "confirmed",
                "notes": fake.sentence(nb_words=6) if random.random() > 0.5 else None
            },
            "status": "pending"
        }

    def generate_batch(self, count: int, distribution: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Generate a batch of events with configurable distribution

        Args:
            count: Number of events to generate
            distribution: Event type distribution, e.g.:
                {
                    "UserCreated": 0.4,      # 40% user events
                    "ActivityCreated": 0.3,  # 30% activity events
                    "ParticipantJoined": 0.3 # 30% participant events
                }

        Returns:
            List of event dictionaries
        """
        if distribution is None:
            # Default distribution
            distribution = {
                "UserCreated": 0.4,
                "UserUpdated": 0.1,
                "ActivityCreated": 0.25,
                "ActivityUpdated": 0.05,
                "ParticipantJoined": 0.2
            }

        # Validate distribution sums to ~1.0
        total = sum(distribution.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Distribution must sum to 1.0, got {total}")

        events = []

        # Generate events based on distribution
        for event_type, proportion in distribution.items():
            event_count = int(count * proportion)

            for _ in range(event_count):
                if event_type == "UserCreated":
                    event = self.generate_user_created_event()
                elif event_type == "UserUpdated":
                    event = self.generate_user_updated_event()
                elif event_type == "ActivityCreated":
                    event = self.generate_activity_created_event()
                elif event_type == "ActivityUpdated":
                    event = self.generate_activity_updated_event()
                elif event_type == "ParticipantJoined":
                    event = self.generate_participant_joined_event()
                else:
                    continue

                # Add created_at timestamp (T0 - our baseline)
                event["created_at"] = datetime.now(timezone.utc).isoformat()
                events.append(event)

        # Shuffle to randomize order
        random.shuffle(events)

        return events

    def reset(self):
        """Reset generated ID tracking"""
        self.generated_user_ids.clear()
        self.generated_activity_ids.clear()


def main():
    """Example usage"""
    generator = EventGenerator()

    print("Generating 10 sample events...")
    events = generator.generate_batch(10)

    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['event_type']}")
        print(f"   Event ID: {event['event_id']}")
        print(f"   Aggregate: {event['aggregate_type']} ({event['aggregate_id']})")
        print(f"   Payload keys: {list(event['payload'].keys())}")


if __name__ == "__main__":
    main()
