import base64
import hashlib
import hmac
from django.conf import settings

def verify_shopify_webhook_hmac(request):
    secret = settings.SHOPIFY_API_SECRET
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
