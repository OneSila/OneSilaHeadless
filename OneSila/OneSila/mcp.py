import asyncio
from contextlib import asynccontextmanager

from llm.mcp import FastMCP, McpApiKeyAuth
from properties.mcp import register_property_mcp_tools
from products.mcp import register_product_mcp_tools


mcp = FastMCP(
    name="OneSila",
    instructions=(
        "This server provides company-scoped access to OneSila property and product management tools. "
        "Use read tools to inspect company languages, properties, property values, and products. "
        "Use write tools only after confirming the intended changes."
    ),
    auth=McpApiKeyAuth(),
    mask_error_details=True,
)

register_property_mcp_tools(mcp=mcp)
register_product_mcp_tools(mcp=mcp)


class ManagedFastMCPApp:
    def __init__(self, *, app):
        self.app = app
        self._lock = asyncio.Lock()
        self._lifespan_context = None
        self._started = False

    async def startup(self):
        if self._started:
            return

        async with self._lock:
            if self._started:
                return

            lifespan = getattr(self.app, "lifespan", None)
            if lifespan is not None:
                self._lifespan_context = lifespan(self.app)
                await self._lifespan_context.__aenter__()

            self._started = True

    async def shutdown(self):
        if not self._started:
            return

        async with self._lock:
            if not self._started:
                return

            lifespan_context = self._lifespan_context
            self._lifespan_context = None
            self._started = False

        if lifespan_context is not None:
            await lifespan_context.__aexit__(None, None, None)

    async def __call__(self, scope, receive, send):
        await self.startup()
        await self.app(scope, receive, send)


raw_mcp_app = mcp.http_app(path="/", stateless_http=True)
managed_mcp_app = ManagedFastMCPApp(app=raw_mcp_app)


@asynccontextmanager
async def mcp_lifespan(*, app):
    await managed_mcp_app.startup()
    try:
        yield
    finally:
        await managed_mcp_app.shutdown()
