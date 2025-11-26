from get_absolute_url.helpers import generate_absolute_url
from sales_channels.integrations.shopify.factories.mixins import GetShopifyApiMixin
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, timezone
import shopify
from urllib.parse import urlparse

from sales_channels.signals import refresh_website_pull_models


class GetShopifyRedirectUrlFactory:

    def __init__(self, sales_channel: ShopifySalesChannel):
        self.sales_channel = sales_channel
        self.redirect_url = None

        shopify.Session.setup(
            api_key=self.sales_channel.api_key,
            secret=self.sales_channel.api_secret
        )

    def clean_shop_hostname(self, hostname: str) -> str:
        # Remove protocol and www
        if hostname.startswith("http://") or hostname.startswith("https://"):
            hostname = urlparse(hostname).netloc or hostname

        return hostname.replace("www.", "")

    def validate_hmac(self):
        if not self.sales_channel.is_external_install:
            return

        if not self.sales_channel.hmac or not self.sales_channel.timestamp or not self.sales_channel.host:
            raise ValueError(_("Missing authentication data for Shopify."))

        params = {
            "hmac": self.sales_channel.hmac,
            "timestamp": str(int(self.sales_channel.timestamp)),
            "host": self.sales_channel.host,
            "shop": self.clean_shop_hostname(self.sales_channel.hostname),
        }

        # Validate using the official library
        if not shopify.Session.validate_params(params):
            raise ValueError(_("Invalid Shopify authentication. Please try again."))

    def get_redirect_url(self):
        redirect_uri = f"{generate_absolute_url(trailing_slash=False)}{reverse('integrations:shopify_oauth_callback')}"

        session = shopify.Session(self.sales_channel.hostname, settings.SHOPIFY_API_VERSION)
        self.redirect_url = session.create_permission_url(
            settings.SHOPIFY_SCOPES,
            redirect_uri,
            self.sales_channel.state
        )

    def run(self):
        self.validate_hmac()
        self.get_redirect_url()


class ValidateShopifyAuthFactory(GetShopifyApiMixin):
    def __init__(self, sales_channel: ShopifySalesChannel, shop: str, code: str, hmac: str, timestamp: str, host: str):
        self.sales_channel = sales_channel
        self.shop = shop
        self.code = code
        self.hmac = hmac
        self.timestamp = timestamp
        self.host = host

    def exchange_token(self):
        shopify.Session.setup(
            api_key=self.sales_channel.api_key,
            secret=self.sales_channel.api_secret,
        )
        session = shopify.Session(self.shop, settings.SHOPIFY_API_VERSION)

        try:
            access_token = session.request_token({
                "code": self.code,
                "shop": self.shop,
                "hmac": self.hmac,
                "timestamp": self.timestamp,
                "host": self.host,
                "state": self.sales_channel.state
            })
        except Exception as e:
            raise ValueError(_("Token exchange failed. Please try again or contact support."))

        self.sales_channel.access_token = access_token
        self.sales_channel.save()

    def dispatch_refresh(self):
        refresh_website_pull_models.send(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel
        )

    def validate_access_token(self):

        try:
            self.get_api()
        except Exception as e:
            raise ValueError(_("Invalid Shopify credentials or access token. Please re-authenticate."))

    def run(self):
        self.exchange_token()
        self.validate_access_token()
        self.dispatch_refresh()
