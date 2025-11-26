from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.decorators.clickjacking import xframe_options_exempt

from products.models import Product
from sales_channels.content_templates import (
    build_content_template_context,
    get_sales_channel_content_template_iframe,
    render_sales_channel_content_template,
)
from sales_channels.models.sales_channels import SalesChannelContentTemplate


@xframe_options_exempt
def sales_channel_content_template_preview(request, template_id: int, product_id: int) -> HttpResponse:
    template = get_object_or_404(SalesChannelContentTemplate, id=template_id)
    product = get_object_or_404(Product, id=product_id)

    template_company_id = template.sales_channel.multi_tenant_company_id
    product_company_id = getattr(product, "multi_tenant_company_id", None)
    if template_company_id and product_company_id and template_company_id != product_company_id:
        raise Http404()

    language = template.language
    description = product._get_translated_value(
        field_name="description",
        related_name="translations",
        language=language,
        sales_channel=template.sales_channel,
    )
    title = product._get_translated_value(
        field_name="name",
        related_name="translations",
        language=language,
        sales_channel=template.sales_channel,
    )

    if not template.template.strip():
        return HttpResponse(mark_safe(description or ""))

    context = build_content_template_context(
        product=product,
        sales_channel=template.sales_channel,
        description=description,
        language=language,
        title=title,
    )

    rendered = render_sales_channel_content_template(
        template_string=template.template,
        context=context,
    )

    return HttpResponse(rendered or mark_safe(description or ""))
