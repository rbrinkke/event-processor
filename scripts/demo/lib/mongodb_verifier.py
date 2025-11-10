"""
MongoDB Verifier - Data Integrity Validation
Verifies that events were correctly processed and stored in MongoDB
"""

import os
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from datetime import datetime


class MongoDBVerifier:
    """
    Verify event processing results in MongoDB

    Checks:
    - Document counts match expected
    - All required fields present
    - Referential integrity (user_id exists for activities/participants)
    - No duplicate events
    - Data completeness
    """

    def __init__(self, mongodb_uri: Optional[str] = None, database: str = "activity_read"):
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database

        # Connect to MongoDB
        self.client = MongoClient(self.mongodb_uri)
        self.db = self.client[self.database_name]

        # Collections
        self.users = self.db.users
        self.activities = self.db.activities
        self.statistics = self.db.statistics

    def verify_counts(self, expected_users: int, expected_activities: int) -> Dict[str, Any]:
        """
        Verify document counts

        Args:
            expected_users: Expected number of users
            expected_activities: Expected number of activities

        Returns:
            Dictionary with count verification results
        """
        actual_users = self.users.count_documents({})
        actual_activities = self.activities.count_documents({})

        users_match = actual_users >= expected_users  # >= because updates don't create new docs
        activities_match = actual_activities >= expected_activities

        return {
            "users": {
                "expected": expected_users,
                "actual": actual_users,
                "match": users_match
            },
            "activities": {
                "expected": expected_activities,
                "actual": actual_activities,
                "match": activities_match
            },
            "overall_match": users_match and activities_match
        }

    def verify_user_documents(self) -> Dict[str, Any]:
        """
        Verify user documents have all required fields

        Returns:
            Dictionary with verification results
        """
        required_fields = ["user_id", "email", "username", "first_name", "last_name", "created_at"]
        users = list(self.users.find({}))

        total_users = len(users)
        complete_users = 0
        missing_fields = []

        for user in users:
            is_complete = all(field in user for field in required_fields)
            if is_complete:
                complete_users += 1
            else:
                user_missing = [field for field in required_fields if field not in user]
                missing_fields.extend(user_missing)

        completeness = (complete_users / total_users * 100) if total_users > 0 else 0

        return {
            "total_users": total_users,
            "complete_users": complete_users,
            "completeness_percentage": round(completeness, 2),
            "missing_fields_count": len(missing_fields),
            "unique_missing_fields": list(set(missing_fields))
        }

    def verify_activity_documents(self) -> Dict[str, Any]:
        """
        Verify activity documents have all required fields

        Returns:
            Dictionary with verification results
        """
        required_fields = ["activity_id", "title", "creator_id", "created_at"]
        activities = list(self.activities.find({}))

        total_activities = len(activities)
        complete_activities = 0
        missing_fields = []

        for activity in activities:
            is_complete = all(field in activity for field in required_fields)
            if is_complete:
                complete_activities += 1
            else:
                activity_missing = [field for field in required_fields if field not in activity]
                missing_fields.extend(activity_missing)

        completeness = (complete_activities / total_activities * 100) if total_activities > 0 else 0

        return {
            "total_activities": total_activities,
            "complete_activities": complete_activities,
            "completeness_percentage": round(completeness, 2),
            "missing_fields_count": len(missing_fields),
            "unique_missing_fields": list(set(missing_fields))
        }

    def verify_referential_integrity(self) -> Dict[str, Any]:
        """
        Verify referential integrity

        Checks:
        - All activity creator_ids exist in users
        - All participant user_ids exist in users

        Returns:
            Dictionary with integrity check results
        """
        all_user_ids = set(user["user_id"] for user in self.users.find({}, {"user_id": 1}))

        # Check activity creators
        invalid_creators = []
        activities = list(self.activities.find({}, {"activity_id": 1, "creator_id": 1}))

        for activity in activities:
            creator_id = activity.get("creator_id")
            if creator_id and creator_id not in all_user_ids:
                invalid_creators.append({
                    "activity_id": activity["activity_id"],
                    "creator_id": creator_id
                })

        # Check participants
        invalid_participants = []
        for activity in self.activities.find({}, {"activity_id": 1, "participants.allowed_users": 1}):
            allowed_users = activity.get("participants", {}).get("allowed_users", [])
            for user_id in allowed_users:
                if user_id not in all_user_ids:
                    invalid_participants.append({
                        "activity_id": activity["activity_id"],
                        "user_id": user_id
                    })

        creator_integrity = len(invalid_creators) == 0
        participant_integrity = len(invalid_participants) == 0

        return {
            "creator_integrity": {
                "valid": creator_integrity,
                "invalid_count": len(invalid_creators),
                "invalid_references": invalid_creators[:5]  # First 5 examples
            },
            "participant_integrity": {
                "valid": participant_integrity,
                "invalid_count": len(invalid_participants),
                "invalid_references": invalid_participants[:5]
            },
            "overall_integrity": creator_integrity and participant_integrity
        }

    def verify_no_duplicates(self) -> Dict[str, Any]:
        """
        Check for duplicate documents

        Returns:
            Dictionary with duplicate check results
        """
        # Check user duplicates
        user_pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        user_duplicates = list(self.users.aggregate(user_pipeline))

        # Check activity duplicates
        activity_pipeline = [
            {"$group": {"_id": "$activity_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        activity_duplicates = list(self.activities.aggregate(activity_pipeline))

        return {
            "users": {
                "has_duplicates": len(user_duplicates) > 0,
                "duplicate_count": len(user_duplicates),
                "examples": user_duplicates[:5]
            },
            "activities": {
                "has_duplicates": len(activity_duplicates) > 0,
                "duplicate_count": len(activity_duplicates),
                "examples": activity_duplicates[:5]
            },
            "no_duplicates": len(user_duplicates) == 0 and len(activity_duplicates) == 0
        }

    def verify_statistics(self) -> Dict[str, Any]:
        """
        Verify statistics collection if it exists

        Returns:
            Dictionary with statistics check results
        """
        stats_doc = self.statistics.find_one({})

        if not stats_doc:
            return {
                "exists": False,
                "message": "No statistics document found"
            }

        return {
            "exists": True,
            "total_users": stats_doc.get("total_users", 0),
            "total_activities": stats_doc.get("total_activities", 0),
            "last_updated": stats_doc.get("last_updated")
        }

    def run_full_verification(self, expected_users: int = 0, expected_activities: int = 0) -> Dict[str, Any]:
        """
        Run complete verification suite

        Args:
            expected_users: Expected user count
            expected_activities: Expected activity count

        Returns:
            Complete verification results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "database": self.database_name,
            "counts": self.verify_counts(expected_users, expected_activities),
            "user_completeness": self.verify_user_documents(),
            "activity_completeness": self.verify_activity_documents(),
            "referential_integrity": self.verify_referential_integrity(),
            "duplicates": self.verify_no_duplicates(),
            "statistics": self.verify_statistics()
        }

        # Overall pass/fail
        results["passed"] = all([
            results["counts"]["overall_match"],
            results["user_completeness"]["completeness_percentage"] == 100,
            results["activity_completeness"]["completeness_percentage"] == 100,
            results["referential_integrity"]["overall_integrity"],
            results["duplicates"]["no_duplicates"]
        ])

        return results

    def print_verification_report(self, results: Dict[str, Any]):
        """Print human-readable verification report"""
        print("\n" + "=" * 70)
        print("MONGODB VERIFICATION REPORT")
        print("=" * 70)

        print(f"\nTimestamp: {results['timestamp']}")
        print(f"Database: {results['database']}")

        # Counts
        counts = results["counts"]
        print(f"\nDocument Counts:")
        print(f"  Users: {counts['users']['actual']} (expected ≥{counts['users']['expected']}) " +
              ("✓" if counts['users']['match'] else "✗"))
        print(f"  Activities: {counts['activities']['actual']} " +
              f"(expected ≥{counts['activities']['expected']}) " +
              ("✓" if counts['activities']['match'] else "✗"))

        # Completeness
        user_comp = results["user_completeness"]
        activity_comp = results["activity_completeness"]
        print(f"\nData Completeness:")
        print(f"  Users: {user_comp['completeness_percentage']}% " +
              ("✓" if user_comp['completeness_percentage'] == 100 else "✗"))
        print(f"  Activities: {activity_comp['completeness_percentage']}% " +
              ("✓" if activity_comp['completeness_percentage'] == 100 else "✗"))

        # Referential Integrity
        integrity = results["referential_integrity"]
        print(f"\nReferential Integrity:")
        print(f"  Creator references: " +
              ("✓ Valid" if integrity['creator_integrity']['valid'] else
               f"✗ {integrity['creator_integrity']['invalid_count']} invalid"))
        print(f"  Participant references: " +
              ("✓ Valid" if integrity['participant_integrity']['valid'] else
               f"✗ {integrity['participant_integrity']['invalid_count']} invalid"))

        # Duplicates
        duplicates = results["duplicates"]
        print(f"\nDuplicate Check:")
        print(f"  Users: " +
              ("✓ No duplicates" if not duplicates['users']['has_duplicates'] else
               f"✗ {duplicates['users']['duplicate_count']} duplicates"))
        print(f"  Activities: " +
              ("✓ No duplicates" if not duplicates['activities']['has_duplicates'] else
               f"✗ {duplicates['activities']['duplicate_count']} duplicates"))

        # Overall
        print(f"\n{'=' * 70}")
        if results["passed"]:
            print("OVERALL RESULT: ✓ ALL CHECKS PASSED")
        else:
            print("OVERALL RESULT: ✗ SOME CHECKS FAILED")
        print("=" * 70)

    def cleanup(self):
        """Close MongoDB connection"""
        self.client.close()


def main():
    """Example usage"""
    verifier = MongoDBVerifier()

    print("Running MongoDB verification...")
    results = verifier.run_full_verification(expected_users=10, expected_activities=5)

    verifier.print_verification_report(results)
    verifier.cleanup()


if __name__ == "__main__":
    main()
