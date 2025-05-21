import binascii
import shopify
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from sales_channels.integrations.shopify.models import ShopifySalesChannel, ShopifySalesChannelView
from sales_channels.signals import refresh_website_pull_models
import logging
import json

logger = logging.getLogger(__name__)

def shopify_auth_start(request):
    shop = request.GET.get("shop")
    state = request.GET.get("state")

    if not shop or not state:
        return HttpResponseBadRequest("Missing 'shop' or 'state' parameter")

    # Verify the state exists in a sales channel for this company
    # if not ShopifySalesChannel.objects.filter(state=state, multi_tenant_company=request.user.multi_tenant_company).exists():
    #     return HttpResponse("Invalid or expired state", status=403)

    # Setup Shopify session
    shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_API_SECRET)

    # Build the redirect URI dynamically
    redirect_uri = request.build_absolute_uri(reverse('shopify:shopify_oauth_callback'))
    # if settings.DEBUG:
    #     redirect_uri = settings.SHOPIFY_TEST_REDIRECT_URI

    # Create permission URL
    session = shopify.Session(shop, settings.SHOPIFY_API_VERSION)
    permission_url = session.create_permission_url(settings.SHOPIFY_SCOPES, redirect_uri, state)

    return redirect(permission_url)


@csrf_exempt
def shopify_auth_callback(request):
    shop = request.GET.get("shop")
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not all([shop, code, state]):
        return HttpResponseBadRequest("Missing parameters")

    # Setup session
    shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_API_SECRET)
    session = shopify.Session(shop, settings.SHOPIFY_API_VERSION)

    try:
        access_token = session.request_token(request.GET)
    except Exception as e:
        return HttpResponse(f"Token exchange failed: {e}", status=500)

    # Validate the state and store access token
    try:
        sales_channel = ShopifySalesChannel.objects.get(state=state)
        sales_channel.access_token = access_token
        sales_channel.save()

        # start pull essential data from the sales channel
        refresh_website_pull_models.send(sender=sales_channel.__class__, instance=sales_channel)
    except ShopifySalesChannel.DoesNotExist:
        return HttpResponse("Sales channel not found for state", status=404)

    # Optional: validate session works
    shopify.ShopifyResource.activate_session(session)
    try:
        shop_info = shopify.Shop.current()
        return redirect(reverse("integrations:integrations_list"))
    finally:
        shopify.ShopifyResource.clear_session()


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