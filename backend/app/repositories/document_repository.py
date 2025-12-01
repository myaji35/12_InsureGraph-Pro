"""
Document Repository

Data access layer for documents table (MVP search).
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from loguru import logger

from app.core.database import PostgreSQLManager


class DocumentFilter:
    """Filter parameters for document search"""

    def __init__(
        self,
        query: Optional[str] = None,
        insurer: Optional[str] = None,
        amount_min: Optional[int] = None,
        amount_max: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ):
        self.query = query
        self.insurer = insurer
        self.amount_min = amount_min
        self.amount_max = amount_max
        self.limit = limit
        self.offset = offset


class DocumentRepository:
    """Repository for documents data access"""

    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager

    def create(
        self,
        policy_name: str,
        insurer: str,
        full_text: str,
        parsed_structure: Dict[str, Any],
        critical_data: Dict[str, Any],
        policy_id: Optional[UUID] = None,
        **metadata
    ) -> Dict[str, Any]:
        """
        Create a new document.

        Args:
            policy_name: Insurance policy name
            insurer: Insurance company name
            full_text: Full extracted text from PDF
            parsed_structure: Parsed legal structure (ParsedDocument as dict)
            critical_data: Extracted critical data (ExtractionResult as dict)
            policy_id: Optional reference to policy_metadata
            **metadata: Additional metadata (total_pages, total_chars, etc.)

        Returns:
            Created document as dict

        Raises:
            Exception: If database operation fails
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                INSERT INTO documents (
                    policy_name, insurer, policy_id, full_text,
                    parsed_structure, critical_data,
                    total_pages, total_chars, total_articles, total_paragraphs,
                    total_subclauses, total_amounts, total_periods, total_kcd_codes
                )
                VALUES (
                    %(policy_name)s, %(insurer)s, %(policy_id)s, %(full_text)s,
                    %(parsed_structure)s, %(critical_data)s,
                    %(total_pages)s, %(total_chars)s, %(total_articles)s, %(total_paragraphs)s,
                    %(total_subclauses)s, %(total_amounts)s, %(total_periods)s, %(total_kcd_codes)s
                )
                RETURNING *
            """

            cursor.execute(query, {
                "policy_name": policy_name,
                "insurer": insurer,
                "policy_id": str(policy_id) if policy_id else None,
                "full_text": full_text,
                "parsed_structure": Json(parsed_structure),
                "critical_data": Json(critical_data),
                "total_pages": metadata.get("total_pages", 0),
                "total_chars": metadata.get("total_chars", 0),
                "total_articles": metadata.get("total_articles", 0),
                "total_paragraphs": metadata.get("total_paragraphs", 0),
                "total_subclauses": metadata.get("total_subclauses", 0),
                "total_amounts": metadata.get("total_amounts", 0),
                "total_periods": metadata.get("total_periods", 0),
                "total_kcd_codes": metadata.get("total_kcd_codes", 0),
            })

            row = cursor.fetchone()
            conn.commit()

            logger.info(f"Created document: {row['id']} - {policy_name}")

            return dict(row)

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create document: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def get_by_id(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document dict if found, None otherwise
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = "SELECT * FROM documents WHERE id = %s"
            cursor.execute(query, (str(document_id),))

            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def search(self, filter_params: DocumentFilter) -> List[Dict[str, Any]]:
        """
        Search documents with filters.

        Args:
            filter_params: Search filters

        Returns:
            List of matching documents
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build WHERE conditions
            conditions = []
            params = {}

            # Full-text search
            if filter_params.query:
                conditions.append("search_vector @@ plainto_tsquery('simple', %(query)s)")
                params["query"] = filter_params.query

            # Insurer filter
            if filter_params.insurer:
                conditions.append("insurer = %(insurer)s")
                params["insurer"] = filter_params.insurer

            # Amount range filter (JSONB query)
            if filter_params.amount_min is not None or filter_params.amount_max is not None:
                amount_min = filter_params.amount_min or 0
                amount_max = filter_params.amount_max or 999999999

                conditions.append("""
                    EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(critical_data->'amounts') AS amt
                        WHERE (amt->>'normalized_value')::bigint BETWEEN %(amount_min)s AND %(amount_max)s
                    )
                """)
                params["amount_min"] = amount_min
                params["amount_max"] = amount_max

            # Build final query
            where_clause = " AND ".join(conditions) if conditions else "TRUE"

            query = f"""
                SELECT
                    id, policy_name, insurer, policy_id,
                    total_pages, total_chars, total_articles, total_paragraphs,
                    total_subclauses, total_amounts, total_periods, total_kcd_codes,
                    created_at, updated_at,
                    -- Include relevance score if text search
                    {
                        "ts_rank(search_vector, plainto_tsquery('simple', %(query)s)) AS relevance"
                        if filter_params.query else "0 AS relevance"
                    }
                FROM documents
                WHERE {where_clause}
                ORDER BY {
                    "relevance DESC, created_at DESC"
                    if filter_params.query else "created_at DESC"
                }
                LIMIT %(limit)s OFFSET %(offset)s
            """

            params["limit"] = filter_params.limit
            params["offset"] = filter_params.offset

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def get_full_document(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get document with full_text and JSONB fields.

        Args:
            document_id: Document UUID

        Returns:
            Full document dict if found, None otherwise
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    id, policy_name, insurer, policy_id,
                    full_text, parsed_structure, critical_data,
                    total_pages, total_chars, total_articles, total_paragraphs,
                    total_subclauses, total_amounts, total_periods, total_kcd_codes,
                    created_at, updated_at
                FROM documents
                WHERE id = %s
            """
            cursor.execute(query, (str(document_id),))

            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get full document: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def count(self, filter_params: Optional[DocumentFilter] = None) -> int:
        """
        Count documents matching filter.

        Args:
            filter_params: Optional search filters

        Returns:
            Total count of matching documents
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            if not filter_params:
                query = "SELECT COUNT(*) FROM documents"
                cursor.execute(query)
            else:
                # Build WHERE conditions (same as search)
                conditions = []
                params = {}

                if filter_params.query:
                    conditions.append("search_vector @@ plainto_tsquery('simple', %(query)s)")
                    params["query"] = filter_params.query

                if filter_params.insurer:
                    conditions.append("insurer = %(insurer)s")
                    params["insurer"] = filter_params.insurer

                if filter_params.amount_min is not None or filter_params.amount_max is not None:
                    amount_min = filter_params.amount_min or 0
                    amount_max = filter_params.amount_max or 999999999

                    conditions.append("""
                        EXISTS (
                            SELECT 1
                            FROM jsonb_array_elements(critical_data->'amounts') AS amt
                            WHERE (amt->>'normalized_value')::bigint BETWEEN %(amount_min)s AND %(amount_max)s
                        )
                    """)
                    params["amount_min"] = amount_min
                    params["amount_max"] = amount_max

                where_clause = " AND ".join(conditions) if conditions else "TRUE"
                query = f"SELECT COUNT(*) FROM documents WHERE {where_clause}"
                cursor.execute(query, params)

            count = cursor.fetchone()[0]
            return count

        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def delete(self, document_id: UUID) -> bool:
        """
        Delete document by ID.

        Args:
            document_id: Document UUID

        Returns:
            True if deleted, False if not found
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            query = "DELETE FROM documents WHERE id = %s"
            cursor.execute(query, (str(document_id),))

            deleted = cursor.rowcount > 0
            conn.commit()

            if deleted:
                logger.info(f"Deleted document: {document_id}")

            return deleted

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to delete document: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def get_insurers(self) -> List[str]:
        """
        Get list of unique insurers.

        Returns:
            List of insurer names
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT insurer
                FROM documents
                ORDER BY insurer
            """
            cursor.execute(query)

            rows = cursor.fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get insurers: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)


# Singleton instance
_repository: Optional[DocumentRepository] = None


def get_document_repository(db_manager: Optional[PostgreSQLManager] = None) -> DocumentRepository:
    """Get or create singleton document repository"""
    global _repository

    if _repository is None:
        from app.core.database import pg_manager
        _repository = DocumentRepository(db_manager or pg_manager)

    return _repository
