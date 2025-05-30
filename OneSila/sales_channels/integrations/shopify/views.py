from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import EmptyTemplateView
from sales_channels.integrations.shopify.models import ShopifySalesChannelView
import logging
import json

logger = logging.getLogger(__name__)

class ShopifyInstalledView(EmptyTemplateView):
    pass

class ShopifyEntryView(EmptyTemplateView):
    pass

@csrf_exempt
def shopify_customer_data_request(request):
    logger.info("Received customers/data_request webhook")
    logger.debug(json.loads(request.body))
    return HttpResponse(status=200)


@csrf_exempt
def shopify_customer_redact(request):
    logger.info("Received customers/redact webhook")
    logger.debug(json.loads(request.body))
    return HttpResponse(status=200)


@csrf_exempt
def shopify_shop_redact(request):
    try:
        payload = json.loads(request.body)
        shop_id = str(payload.get("shop_id"))

        logger.info(f"Received shop/redact webhook for shop_id: {shop_id}")

        view = ShopifySalesChannelView.objects.filter(remote_id=shop_id).first()
        if view and view.sales_channel:
            sales_channel = view.sales_channel
            sales_channel.mark_for_delete = True
            sales_channel.save(update_fields=["mark_for_delete"])
            logger.info(f"Marked SalesChannel {view.sales_channel.pk} for delete.")
        else:
            logger.warning(f"No SalesChannelView found with remote_id={shop_id}")

    except Exception as e:
        logger.exception("Error processing shop/redact webhook")
        return HttpResponse(status=400)

    return HttpResponse(status=200)
