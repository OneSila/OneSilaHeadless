"""Placeholder for Shein GraphQL queries."""

import strawberry


@strawberry.type
class SheinQuery:
    """Extend the root query with Shein fields."""

    @strawberry.field
    def shein_placeholder(self, info) -> str:  # pragma: no cover - placeholder
        """Remove once real queries are implemented."""
        raise NotImplementedError
