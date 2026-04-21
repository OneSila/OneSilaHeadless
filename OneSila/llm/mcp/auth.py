from __future__ import annotations

from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from llm.mcp.runtime import AccessToken, TokenVerifier, get_access_token


def get_authenticated_user():
    token = get_access_token()
    if token is None or not token.client_id or not str(token.client_id).startswith("user:"):
        return None

    user_model = get_user_model()
    user_id = int(str(token.client_id).split(":", 1)[1])
    try:
        return user_model.objects.select_related("multi_tenant_company").get(pk=user_id)
    except user_model.DoesNotExist:
        return None


def get_authenticated_company():
    user = get_authenticated_user()
    if user is None:
        return None

    return user.multi_tenant_company


class McpApiKeyAuth(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        mcp_api_key = await self._lookup(token=token)
        if mcp_api_key is None:
            return None

        return AccessToken(
            token=token,
            client_id=f"user:{mcp_api_key.user_id}",
            scopes=[],
        )

    @sync_to_async
    def _lookup(self, *, token: str):
        from llm.models import McpApiKey

        try:
            return McpApiKey.objects.select_related("user").get(
                key=token,
                is_active=True,
            )
        except McpApiKey.DoesNotExist:
            return None
