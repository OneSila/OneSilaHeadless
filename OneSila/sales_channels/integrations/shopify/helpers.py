import base64
import hashlib
import hmac
import json
from sales_channels.integrations.shopify.models import ShopifySalesChannel

def verify_shopify_webhook_hmac(request):
    secret = None
    domain = request.headers.get('X-Shopify-Shop-Domain')
    channel = None

    if domain:
        channel = ShopifySalesChannel.objects.filter(hostname__icontains=domain).first()
    else:
        try:
            payload = json.loads(request.body)
            shop_domain = payload.get('shop_domain')
            if shop_domain:
                channel = ShopifySalesChannel.objects.filter(hostname__icontains=shop_domain).first()
        except Exception:
            pass

    if channel:
        secret = channel.api_secret

    if not secret:
        return False
    shopify_hmac = request.headers.get('X-Shopify-Hmac-Sha256')
    if not shopify_hmac:
        return False

    digest = hmac.new(
        secret.encode('utf-8'),
        request.body,
        hashlib.sha256
    ).digest()

    computed_hmac = base64.b64encode(digest).decode()

    return hmac.compare_digest(computed_hmac, shopify_hmac)
