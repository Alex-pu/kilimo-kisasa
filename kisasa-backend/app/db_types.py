import json
import uuid

from sqlalchemy import CHAR, JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PostgresUUID


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    PostgreSQL keeps native UUIDs. SQLite stores canonical UUID strings.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class StringList(TypeDecorator):
    """List of strings using ARRAY on PostgreSQL and JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return list(value)


class GUIDList(TypeDecorator):
    """List of UUIDs using ARRAY(UUID) on PostgreSQL and JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(PostgresUUID(as_uuid=True)))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return [str(item) for item in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            value = json.loads(value)
        return [uuid.UUID(str(item)) for item in value]
