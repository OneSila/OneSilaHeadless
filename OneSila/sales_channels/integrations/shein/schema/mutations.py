"""Placeholder for Shein GraphQL mutations."""

import strawberry


@strawberry.type(name="Mutation")
class SheinMutation:
    """Extend the root mutation with Shein operations."""

    @strawberry.mutation
    def shein_placeholder_mutation(self, info) -> bool:  # pragma: no cover - placeholder
        """Remove once real mutations are implemented."""
        raise NotImplementedError
