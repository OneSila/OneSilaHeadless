from datetime import timedelta
import traceback

from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from ebay_rest import token

from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.signals import refresh_website_pull_models


class GetEbayRedirectUrlFactory:
    def __init__(self, sales_channel: EbaySalesChannel):
        self.sales_channel = sales_channel
        self.redirect_url = None

    def run(self):
        oauth = token._OAuth2Api(
            sandbox=settings.DEBUG,
            client_id=settings.EBAY_CLIENT_ID,
            client_secret=settings.EBAY_CLIENT_SECRET,
            ru_name=getattr(settings, "EBAY_RU_NAME", None),
        )
        scopes = getattr(settings, "EBAY_APPLICATION_SCOPES", ["https://api.ebay.com/oauth/api_scope"])
        self.redirect_url = oauth.generate_user_authorization_url(
            scopes,
            state=self.sales_channel.state,
        )


class ValidateEbayAuthFactory:
    def __init__(self, sales_channel: EbaySalesChannel, code: str):
        self.sales_channel = sales_channel
        self.code = code

    def exchange_token(self):
        oauth = token._OAuth2Api(
            sandbox=settings.DEBUG,
            client_id=settings.EBAY_CLIENT_ID,
            client_secret=settings.EBAY_CLIENT_SECRET,
            ru_name=getattr(settings, "EBAY_RU_NAME", None),
        )
        try:
            token_obj = oauth.exchange_code_for_access_token(self.code)
        except Exception:
            tb = traceback.format_exc()
            self.sales_channel.connection_error = tb
            self.sales_channel.save(update_fields=["connection_error"])
            raise ValueError(_("Token exchange failed. Please try again or contact support."))

        self.sales_channel.refresh_token = token_obj.refresh_token
        self.sales_channel.access_token = token_obj.access_token
        self.sales_channel.refresh_token_expiration = token_obj.refresh_token_expiry
        self.sales_channel.expiration_date = token_obj.token_expiry
        self.sales_channel.save()

    def dispatch_refresh(self):
        refresh_website_pull_models.send(
            sender=self.sales_channel.__class__,
            instance=self.sales_channel
        )

    def run(self):
        self.exchange_token()
        self.dispatch_refresh()
