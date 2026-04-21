from __future__ import annotations

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field
from typing import Annotated

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_COMPANY, TAG_GET, tool_tags
from products.mcp.company_details_helpers import get_company_details_payload
from products.mcp.output_types import GET_COMPANY_DETAILS_OUTPUT_SCHEMA
from products.mcp.types import CompanyDetailsPayload


class GetCompanyDetailsMcpTool(BaseMcpTool):
    name = "get_company_details"
    title = "Get Company Details"
    read_only = True
    tags = tool_tags(TAG_GET, TAG_COMPANY)
    output_schema = GET_COMPANY_DETAILS_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        show_languages: Annotated[bool, Field(description="Opt in to company languages when you need language codes for translation writes or validation.")] = False,
        show_product_types: Annotated[bool, Field(description="Opt in to product-type values when you need `product_type_id` or `product_type_value` for create or property writes.")] = False,
        show_product_types_translations: Annotated[bool, Field(description="Also include product-type translations. This automatically enables `show_product_types`.")] = False,
        show_product_types_usage_counts: Annotated[bool, Field(description="Also include product-type usage counts. This automatically enables `show_product_types`.")] = False,
        show_vat_rates: Annotated[bool, Field(description="Opt in to configured VAT rates when you need `vat_rate_id` for create or upsert, or when you want to confirm the exact percentage.")] = False,
        show_currencies: Annotated[bool, Field(description="Opt in to company currencies when you need valid currency codes for price writes.")] = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get company reference data with opt-in sections.

        Use this only when you need reference data for a write or validation step:
        - languages for translation writes
        - product types for create-time product type assignment
        - VAT rates for create/upsert VAT assignment
        - currencies for price writes

        Do not use this as a general fallback after `search_products`. It is not a product-count or
        product-inspection tool. If you need a product count, use `search_products`. If you need the
        state of a specific product, use `get_product`.

        Set only the `show_*` flags you need. Each flag opts in to one section of reference data.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            response_data = await self._get_company_details(
                multi_tenant_company=multi_tenant_company,
                show_languages=self.sanitize_optional_bool(
                    value=show_languages,
                    field_name="show_languages",
                ) or False,
                show_product_types=self.sanitize_optional_bool(
                    value=show_product_types,
                    field_name="show_product_types",
                ) or False,
                show_product_types_translations=self.sanitize_optional_bool(
                    value=show_product_types_translations,
                    field_name="show_product_types_translations",
                ) or False,
                show_product_types_usage_counts=self.sanitize_optional_bool(
                    value=show_product_types_usage_counts,
                    field_name="show_product_types_usage_counts",
                ) or False,
                show_vat_rates=self.sanitize_optional_bool(
                    value=show_vat_rates,
                    field_name="show_vat_rates",
                ) or False,
                show_currencies=self.sanitize_optional_bool(
                    value=show_currencies,
                    field_name="show_currencies",
                ) or False,
            )
            await ctx.info(
                f"Loaded company details for company_id={multi_tenant_company.id} "
                f"with sections={sorted(response_data.keys())}."
            )
            return self.build_result(
                summary="Loaded company details.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get company details failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _get_company_details(
        self,
        *,
        multi_tenant_company,
        show_languages: bool,
        show_product_types: bool,
        show_product_types_translations: bool,
        show_product_types_usage_counts: bool,
        show_vat_rates: bool,
        show_currencies: bool,
    ) -> CompanyDetailsPayload:
        try:
            return get_company_details_payload(
                multi_tenant_company=multi_tenant_company,
                show_languages=show_languages,
                show_product_types=show_product_types,
                show_product_types_translations=show_product_types_translations,
                show_product_types_usage_counts=show_product_types_usage_counts,
                show_vat_rates=show_vat_rates,
                show_currencies=show_currencies,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
