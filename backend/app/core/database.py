"""
Database connection managers for PostgreSQL, Neo4j, and Redis
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import register_uuid
from neo4j import GraphDatabase, AsyncGraphDatabase
from redis import Redis
import asyncio

from app.core.config import settings


class PostgreSQLManager:
    """PostgreSQL connection pool manager"""

    def __init__(self):
        self.pool: ThreadedConnectionPool | None = None

    def connect(self):
        """Initialize connection pool"""
        # Register UUID adapter globally for psycopg2
        # This allows psycopg2 to handle Python UUID objects correctly
        register_uuid()

        self.pool = ThreadedConnectionPool(
            minconn=settings.POSTGRES_MIN_CONNECTIONS,
            maxconn=settings.POSTGRES_MAX_CONNECTIONS,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            connect_timeout=settings.POSTGRES_CONNECT_TIMEOUT,
        )
        print(
            "✅ PostgreSQL connection pool created ",
            f"(min={settings.POSTGRES_MIN_CONNECTIONS}, max={settings.POSTGRES_MAX_CONNECTIONS})",
        )

    def disconnect(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            print("✅ PostgreSQL connection pool closed")

    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool"""
        self.pool.putconn(conn)


class Neo4jManager:
    """Neo4j async driver manager"""

    def __init__(self):
        self.driver = None

    async def connect(self):
        """Initialize Neo4j driver"""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
            connection_acquisition_timeout=settings.NEO4J_ACQUISITION_TIMEOUT,
            connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT,
        )
        # Verify connectivity
        await self.driver.verify_connectivity()
        print(
            "✅ Neo4j driver connected ",
            f"(pool_size={settings.NEO4J_MAX_CONNECTION_POOL_SIZE})",
        )

    async def disconnect(self):
        """Close Neo4j driver"""
        if self.driver:
            await self.driver.close()
            print("✅ Neo4j driver closed")

    def get_session(self):
        """Get a new session"""
        return self.driver.session()


class RedisManager:
    """Redis connection manager"""

    def __init__(self):
        self.client: Redis | None = None

    def connect(self):
        """Initialize Redis client"""
        self.client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        )
        # Test connection
        self.client.ping()
        print("✅ Redis client connected")

    def disconnect(self):
        """Close Redis client"""
        if self.client:
            self.client.close()
            print("✅ Redis client closed")


# Global instances
pg_manager = PostgreSQLManager()
neo4j_manager = Neo4jManager()
redis_manager = RedisManager()


# Dependency injection for FastAPI
def get_pg_connection():
    """FastAPI dependency for PostgreSQL connection"""
    conn = pg_manager.get_connection()
    try:
        yield conn
    finally:
        pg_manager.return_connection(conn)


async def get_neo4j_session():
    """FastAPI dependency for Neo4j session"""
    async with neo4j_manager.get_session() as session:
        yield session


def get_redis_client():
    """FastAPI dependency for Redis client"""
    return redis_manager.client
