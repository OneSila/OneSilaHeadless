from __future__ import annotations

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_COMPANY, TAG_GET, TAG_LANGUAGES, tool_tags
from properties.mcp.helpers import serialize_company_languages
from properties.mcp.output_types import GET_COMPANY_LANGUAGES_OUTPUT_SCHEMA
from properties.mcp.types import CompanyLanguagesPayload


class GetCompanyLanguagesMcpTool(BaseMcpTool):
    name = "get_company_languages"
    title = "Get Company Languages"
    read_only = True
    tags = tool_tags(TAG_GET, TAG_COMPANY, TAG_LANGUAGES)
    output_schema = GET_COMPANY_LANGUAGES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get the enabled languages for the authenticated company, including the default language.
        Use this before creating or editing translations so you only send language codes that
        are enabled for the current company.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            response_data: CompanyLanguagesPayload = serialize_company_languages(
                multi_tenant_company=multi_tenant_company,
            )
            await ctx.info(
                f"Loaded {len(response_data['enabled_languages'])} enabled languages "
                f"for company_id={multi_tenant_company.id}."
            )
            return self.build_result(
                summary=(
                    f"Company has {len(response_data['enabled_languages'])} enabled languages. "
                    f"Default language is {response_data['default_language_code']}."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get company languages failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise
