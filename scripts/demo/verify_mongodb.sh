#!/bin/bash
# Quick MongoDB Verification Script
# Check if events made it to MongoDB

MONGODB_URI=${MONGODB_URI:-"mongodb://localhost:27025"}
MONGODB_DATABASE=${MONGODB_DATABASE:-"activity_read"}

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║           MONGODB VERIFICATION - Quick Check                      ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Connecting to: $MONGODB_URI"
echo "Database: $MONGODB_DATABASE"
echo ""

python3 <<EOF
from pymongo import MongoClient
import os

# Connect
uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27025')
db_name = os.getenv('MONGODB_DATABASE', 'activity_read')

client = MongoClient(uri)
db = client[db_name]

print("="*70)
print("COLLECTIONS")
print("="*70)

# Users
user_count = db.users.count_documents({})
print(f"\n✓ Users collection: {user_count} documents")

if user_count > 0:
    users = list(db.users.find({}, {'_id': 0, 'username': 1, 'email': 1, 'created_at': 1}).limit(5))
    print("\n  Recent users:")
    for user in users:
        print(f"    - {user.get('username')}: {user.get('email')}")

# Activities
activity_count = db.activities.count_documents({})
print(f"\n✓ Activities collection: {activity_count} documents")

if activity_count > 0:
    activities = list(db.activities.find({}, {'_id': 0, 'title': 1, 'activity_type': 1, 'created_at': 1}).limit(5))
    print("\n  Recent activities:")
    for activity in activities:
        print(f"    - {activity.get('title')} ({activity.get('activity_type')})")

# Statistics
if 'statistics' in db.list_collection_names():
    stats_count = db.statistics.count_documents({})
    print(f"\n✓ Statistics collection: {stats_count} documents")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total users: {user_count}")
print(f"Total activities: {activity_count}")
print(f"\n{'✓ Data found in MongoDB!' if (user_count > 0 or activity_count > 0) else '✗ No data found'}")
print("="*70)

client.close()
EOF
