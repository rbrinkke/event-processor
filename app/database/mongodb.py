"""
MongoDB Connection Manager
Async MongoDB client met connection pooling
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


class MongoDBManager:
    """
    MongoDB Connection Manager
    Singleton pattern voor hergebruikbare database connectie
    """

    _instance: Optional["MongoDBManager"] = None
    _client: Optional[AsyncIOMotorClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Establish MongoDB connection"""
        if self._client is None:
            try:
                self._client = AsyncIOMotorClient(
                    settings.mongodb_uri,
                    connectTimeoutMS=settings.mongodb_connect_timeout_ms,
                    serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
                )
                # Test connection
                await self._client.admin.command("ping")
                logger.info(
                    "mongodb_connected",
                    uri=settings.mongodb_uri.split("@")[-1],  # Hide credentials
                    database=settings.mongodb_database,
                )
            except Exception as e:
                logger.error("mongodb_connection_failed", error=str(e))
                raise

    async def disconnect(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("mongodb_disconnected")

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get MongoDB client"""
        if self._client is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._client

    @property
    def db(self):
        """Get database instance"""
        return self.client[settings.mongodb_database]

    def collection(self, name: str):
        """Get collection by name"""
        return self.db[name]


# Global MongoDB manager instance
mongodb = MongoDBManager()
