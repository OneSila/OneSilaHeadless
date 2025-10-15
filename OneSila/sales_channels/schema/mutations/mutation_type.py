from typing import Optional, Annotated

from django.template import TemplateSyntaxError
from strawberry import Info, lazy
import strawberry_django

from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.mutations import create, update, delete, type, List, field
from .fields import resync_sales_channel_assign, refresh_website_models_mutation
from ..types.types import SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, \
    SalesChannelViewAssignType, SalesChannelContentTemplateType, SalesChannelImportType, RemoteLanguageType, \
    RemoteCurrencyType, ImportPropertyType, SalesChannelContentTemplateCheckType, FormattedIssueType
from ..types.input import SalesChannelImportInput, SalesChannelImportPartialInput, SalesChannelInput, \
    SalesChannelPartialInput, \
    SalesChannelIntegrationPricelistInput, SalesChannelIntegrationPricelistPartialInput, SalesChannelViewInput, \
    SalesChannelViewPartialInput, SalesChannelViewAssignInput, SalesChannelViewAssignPartialInput, \
    SalesChannelContentTemplateInput, SalesChannelContentTemplatePartialInput, \
    RemoteLanguagePartialInput, RemoteCurrencyPartialInput, ImportPropertyInput
from .validators import validate_sku_conflicts, validate_amazon_assignment
from core.helpers import get_languages
from products.models import Product
from sales_channels.content_templates import (
    build_content_template_context,
    render_sales_channel_content_template,
)
from sales_channels.models import SalesChannel


@type(name='Mutation')
class SalesChannelsMutation:
    create_sales_import_process: SalesChannelImportType = create(SalesChannelImportInput)
    create_sales_import_processes: List[SalesChannelImportType] = create(SalesChannelImportInput)
    update_sales_import_process: SalesChannelImportType = update(SalesChannelImportPartialInput)
    delete_sales_import_process: SalesChannelImportType = delete()
    delete_sales_import_processes: List[SalesChannelImportType] = delete()

    create_sales_channel: SalesChannelType = create(SalesChannelInput)
    create_sales_channels: List[SalesChannelType] = create(SalesChannelInput)
    update_sales_channel: SalesChannelType = update(SalesChannelPartialInput)
    delete_sales_channel: SalesChannelType = delete()
    delete_sales_channels: List[SalesChannelType] = delete()
    refresh_sales_channel_websites: SalesChannelType = refresh_website_models_mutation()

    create_sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = create(SalesChannelIntegrationPricelistInput)
    create_sales_channel_integration_pricelists: List[SalesChannelIntegrationPricelistType] = create(List[SalesChannelIntegrationPricelistInput])
    update_sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = update(SalesChannelIntegrationPricelistPartialInput)
    delete_sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = delete()
    delete_sales_channel_integration_pricelists: List[SalesChannelIntegrationPricelistType] = delete()

    update_sales_channel_view: SalesChannelViewType = update(SalesChannelViewPartialInput)
    update_remote_language: RemoteLanguageType = update(RemoteLanguagePartialInput)
    update_remote_currency: RemoteCurrencyType = update(RemoteCurrencyPartialInput)

    # Language Bulk Update
    update_remote_languages: List[RemoteLanguageType] = update(List[RemoteLanguagePartialInput])

    # Currency Bulk Update
    update_remote_currencies: List[RemoteCurrencyType] = update(List[RemoteCurrencyPartialInput])

    create_import_properties: List[ImportPropertyType] = create(List[ImportPropertyInput])

    create_sales_channel_content_template: SalesChannelContentTemplateType = create(SalesChannelContentTemplateInput)
    create_sales_channel_content_templates: List[SalesChannelContentTemplateType] = create(List[SalesChannelContentTemplateInput])
    update_sales_channel_content_template: SalesChannelContentTemplateType = update(SalesChannelContentTemplatePartialInput)
    delete_sales_channel_content_template: SalesChannelContentTemplateType = delete()
    delete_sales_channel_content_templates: List[SalesChannelContentTemplateType] = delete()

    create_sales_channel_view_assign: SalesChannelViewAssignType = create(
        SalesChannelViewAssignInput,
        validators=[validate_sku_conflicts, validate_amazon_assignment],
    )
    resync_sales_channel_view_assign: SalesChannelViewAssignType = resync_sales_channel_assign()
    create_sales_channel_view_assigns: List[SalesChannelViewAssignType] = create(
        SalesChannelViewAssignInput,
        validators=[validate_sku_conflicts, validate_amazon_assignment],
    )
    update_sales_channel_view_assign: SalesChannelViewAssignType = update(SalesChannelViewAssignPartialInput)
    delete_sales_channel_view_assign: SalesChannelViewAssignType = delete()
    delete_sales_channel_view_assigns: List[SalesChannelViewAssignType] = delete()

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def check_sales_channel_content_template(
        self,
        info: Info,
        *,
        sales_channel: SalesChannelPartialInput,
        template: str,
        language: str,
        product: Annotated['ProductPartialInput', lazy("products.schema.types.input")],
    ) -> SalesChannelContentTemplateCheckType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        try:
            channel = SalesChannel.objects.get(
                id=sales_channel.id.node_id,
                multi_tenant_company=multi_tenant_company,
            )
        except SalesChannel.DoesNotExist as exc:
            raise PermissionError("Invalid company") from exc

        language_code = language
        available_languages = {code for code, _ in get_languages()}

        if language_code not in available_languages:
            return SalesChannelContentTemplateCheckType(
                is_valid=False,
                rendered_content=None,
                available_variables=[],
                errors=[
                    FormattedIssueType(
                        message=f"Unsupported language '{language_code}'.",
                        severity="ERROR",
                        validation_issue=True,
                    )
                ],
            )

        try:
            product_instance = Product.objects.get(
                id=product.id.node_id,
                multi_tenant_company=multi_tenant_company,
            )
        except Product.DoesNotExist:
            return SalesChannelContentTemplateCheckType(
                is_valid=False,
                rendered_content=None,
                available_variables=[],
                errors=[
                    FormattedIssueType(
                        message="The selected product is not available.",
                        severity="ERROR",
                        validation_issue=True,
                    )
                ],
            )

        description = product_instance._get_translated_value(
            field_name='description',
            language=language_code,
            related_name='translations',
            sales_channel=channel,
        )

        title = product_instance._get_translated_value(
            field_name='name',
            language=language_code,
            related_name='translations',
            sales_channel=channel,
        )

        context = build_content_template_context(
            product=product_instance,
            sales_channel=channel,
            description=description,
            language=language_code,
            title=title or "",
        )

        available_variables = sorted(context.keys())

        if not template.strip():
            return SalesChannelContentTemplateCheckType(
                is_valid=True,
                rendered_content=description,
                available_variables=available_variables,
                errors=[],
            )

        try:
            rendered = render_sales_channel_content_template(
                template_string=template,
                context=context,
            )
        except TemplateSyntaxError as exc:
            return SalesChannelContentTemplateCheckType(
                is_valid=False,
                rendered_content=None,
                available_variables=available_variables,
                errors=[
                    FormattedIssueType(
                        message=str(exc),
                        severity="ERROR",
                        validation_issue=True,
                    )
                ],
            )
        except Exception as exc:  # pragma: no cover - unexpected rendering error
            return SalesChannelContentTemplateCheckType(
                is_valid=False,
                rendered_content=None,
                available_variables=available_variables,
                errors=[
                    FormattedIssueType(
                        message=str(exc),
                        severity="ERROR",
                        validation_issue=False,
                    )
                ],
            )

        return SalesChannelContentTemplateCheckType(
            is_valid=True,
            rendered_content=rendered,
            available_variables=available_variables,
            errors=[],
        )
