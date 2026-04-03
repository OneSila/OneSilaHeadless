from __future__ import annotations

from asgiref.sync import sync_to_async

from llm.mcp.runtime import AccessToken, TokenVerifier, get_access_token


def get_authenticated_company():
    token = get_access_token()
    if token is None or not token.client_id or not str(token.client_id).startswith("company:"):
        return None

    from core.models import MultiTenantCompany

    company_id = int(str(token.client_id).split(":", 1)[1])
    try:
        return MultiTenantCompany.objects.get(pk=company_id)
    except MultiTenantCompany.DoesNotExist:
        return None


class McpApiKeyAuth(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        mcp_api_key = await self._lookup(token=token)
        if mcp_api_key is None:
            return None

        return AccessToken(
            token=token,
            client_id=f"company:{mcp_api_key.multi_tenant_company_id}",
            scopes=[],
        )

    @sync_to_async
    def _lookup(self, *, token: str):
        from llm.models import McpApiKey

        try:
            return McpApiKey.objects.select_related("multi_tenant_company").get(
                key=token,
                is_active=True,
            )
        except McpApiKey.DoesNotExist:
            return None
