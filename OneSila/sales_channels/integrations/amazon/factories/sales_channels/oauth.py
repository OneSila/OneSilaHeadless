from urllib.parse import urlencode
import json
from datetime import timedelta
from urllib import request, parse

from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from get_absolute_url.helpers import generate_absolute_url
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.constants import SELLER_CENTRAL_URLS, AMAZON_OAUTH_TOKEN_URL
from sales_channels.signals import refresh_website_pull_models


class GetAmazonRedirectUrlFactory:
    def __init__(self, sales_channel: AmazonSalesChannel):
        self.sales_channel = sales_channel
        self.redirect_url = None

    def get_base_url(self) -> str:
        base = SELLER_CENTRAL_URLS.get(self.sales_channel.country)
        if not base:
            raise ValueError(_("Unknown Amazon country."))
        return base

    def run(self):
        params = {
            "application_id": settings.AMAZON_APP_ID,
            "state": self.sales_channel.state,
        }
        if settings.DEBUG:
            params["version"] = "beta"
        base_url = self.get_base_url()
        self.redirect_url = f"{base_url}/apps/authorize/consent?{urlencode(params)}"


class ValidateAmazonAuthFactory:
    def __init__(self, sales_channel: AmazonSalesChannel, code: str, selling_partner_id: str):
        self.sales_channel = sales_channel
        self.code = code
        self.selling_partner_id = selling_partner_id

    def exchange_token(self):
        redirect_uri = f"{generate_absolute_url(trailing_slash=False)}{reverse('integrations:amazon_oauth_callback')}"
        data = parse.urlencode({
            "grant_type": "authorization_code",
            "code": self.code,
            "client_id": settings.AMAZON_CLIENT_ID,
            "client_secret": settings.AMAZON_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
        }).encode()
        req = request.Request(AMAZON_OAUTH_TOKEN_URL, data=data)
        try:
            with request.urlopen(req) as resp:
                payload = json.loads(resp.read())
        except Exception:
            raise ValueError(_("Token exchange failed. Please try again or contact support."))

        self.sales_channel.refresh_token = payload.get("refresh_token")
        self.sales_channel.access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if expires_in:
            self.sales_channel.expiration_date = now() + timedelta(seconds=int(expires_in))
        self.sales_channel.save()

    def dispatch_refresh(self):
        refresh_website_pull_models.send(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel
        )

    def run(self):
        self.exchange_token()
        self.dispatch_refresh()
