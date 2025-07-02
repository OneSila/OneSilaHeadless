import json
import re

from spapi import ListingsApi
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin, AmazonListingIssuesMixin
from sales_channels.integrations.amazon.factories.properties.mixins import AmazonRemoteValueMixin
from sales_channels.integrations.amazon.models.properties import (
    AmazonProductProperty,
    AmazonProperty,
    AmazonProductType,
    AmazonPublicDefinition,
)

from sales_channels.factories.properties.properties import (
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyUpdateFactory,
    RemoteProductPropertyDeleteFactory,
)
from properties.models import ProductProperty


TOKEN_RE = re.compile(r"%([a-z_]+):([^%]+)%")


class AmazonProductPropertyBase(GetAmazonAPIMixin, AmazonRemoteValueMixin, AmazonListingIssuesMixin):
    """Common helpers for Amazon product property factories."""
    pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_remote_property(self) -> AmazonProperty:
        return AmazonProperty.objects.get(
            sales_channel=self.sales_channel,
            local_instance=self.local_property,
        )

    def _get_product_type(self, rule) -> AmazonProductType:
        return AmazonProductType.objects.get(
            sales_channel=self.sales_channel,
            local_instance=rule,
        )

    def _get_public_definition(self, product_type: AmazonProductType, main_code: str) -> AmazonPublicDefinition:
        return AmazonPublicDefinition.objects.get(
            api_region_code=self.view.api_region_code,
            product_type_code=product_type.product_type_code,
            code=main_code,
        )

    def _get_unit(self, code: str):
        from sales_channels.integrations.amazon.models.sales_channels import AmazonDefaultUnitConfigurator

        cfg = AmazonDefaultUnitConfigurator.objects.filter(
            sales_channel=self.sales_channel,
            marketplace=self.view,
            code=code,
        ).first()
        return cfg.selected_unit if cfg else None

    def _replace_tokens(self, data: dict, product) -> dict:
        def _resolve(value: str):
            m = TOKEN_RE.fullmatch(value)
            if not m:
                return value
            kind, code = m.groups()
            if kind == "auto":
                if code == "marketplace_id":
                    return self.view.remote_id
                if code == "language":
                    return self.view.language_tag
                return None
            if kind == "unit":
                return self._get_unit(code)
            if kind == "value":
                remote_prop = AmazonProperty.objects.get(
                    sales_channel=self.sales_channel, code=code
                )
                local_prop = remote_prop.local_instance
                prop_instance = ProductProperty.objects.get(
                    product=product, property=local_prop
                )
                return self.get_remote_value_for_property(prop_instance, remote_prop)
            return value

        def _walk(node):
            if isinstance(node, dict):
                return {k: _walk(v) for k, v in node.items()}
            if isinstance(node, list):
                return [_walk(v) for v in node]
            if isinstance(node, str):
                return _resolve(node)
            return node

        return _walk(data)

    # ------------------------------------------------------------------
    def build_payload(self):
        remote_property = self._get_remote_property()
        main_code = remote_property.main_code
        rule = self.local_instance.product.get_product_rule()
        if not rule:
            raise ValueError("Product has no product rule mapped")
        product_type = self._get_product_type(rule)
        public_def = self._get_public_definition(product_type, main_code)
        if not public_def.usage_definition:
            raise ValueError("Missing usage definition for property")
        usage = json.loads(public_def.usage_definition)

        payload = self._replace_tokens(usage, self.local_instance.product)
        return product_type.product_type_code, payload

    # ------------------------------------------------------------------
    def preflight_check(self):
        if not super().preflight_check():
            return False
        try:
            self._get_remote_property()
        except AmazonProperty.DoesNotExist:
            raise ValueError("Property not mapped to Amazon")
        return True

    def create_body(self):
        product_type_code, payload = self.build_payload()

        self.remote_value = json.dumps(payload)

        if self.get_value_only:
            if self.remote_instance:
                self.remote_instance.remote_value = self.remote_value
                self.remote_instance.save()
            return None

        body = {
            "productType": product_type_code,
            "requirements": "LISTING",
            "attributes": payload,
        }
        self.value = body
        return body


class AmazonProductPropertyCreateFactory(AmazonProductPropertyBase, RemoteProductPropertyCreateFactory):
    remote_model_class = AmazonProductProperty

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, skip_checks=False, get_value_only=False, language=None):
        self.view = view
        super().__init__(sales_channel, local_instance, remote_product=remote_product, api=api, skip_checks=skip_checks, get_value_only=get_value_only, language=language)

    def create_remote(self):
        body = self.create_body()
        if body is None:
            return
        api = self.get_api()
        listings = ListingsApi(self._get_client())
        response = listings.patch_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=self.remote_product.remote_sku,
            marketplace_ids=[self.view.remote_id],
            body=body,
        )
        self.update_assign_issues(getattr(response, "issues", []))
        return response

    def serialize_response(self, response):
        return json.dumps(response.payload) if hasattr(response, "payload") else True

    def post_create_process(self):
        super().post_create_process()


class AmazonProductPropertyUpdateFactory(AmazonProductPropertyBase, RemoteProductPropertyUpdateFactory):
    remote_model_class = AmazonProductProperty
    create_factory_class = AmazonProductPropertyCreateFactory

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, get_value_only=False, remote_instance=None, skip_checks=False, language=None):
        self.view = view
        super().__init__(sales_channel, local_instance, remote_product=remote_product, api=api,
              get_value_only=get_value_only, remote_instance=remote_instance, skip_checks=skip_checks, language=language)

    def update_remote(self):
        body = self.create_body()
        if body is None:
            return
        api = self.get_api()
        listings = ListingsApi(self._get_client())
        response = listings.patch_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=self.remote_product.remote_sku,
            marketplace_ids=[self.view.remote_id],
            body=body,
        )
        self.update_assign_issues(getattr(response, "issues", []))
        return response

    def serialize_response(self, response):
        return json.dumps(response.payload) if hasattr(response, "payload") else True

    def additional_update_check(self):
        self.local_property = self.local_instance.property
        self.remote_product = self.remote_instance.remote_product
        self.remote_property = self.remote_instance.remote_property

        product_type_code, payload = self.build_payload()
        self.remote_value = json.dumps(payload)

        if self.get_value_only:
            self.remote_instance.remote_value = self.remote_value
            self.remote_instance.save()
            return False

        return self.remote_instance.needs_update(self.remote_value)


class AmazonProductPropertyDeleteFactory(AmazonProductPropertyBase, RemoteProductPropertyDeleteFactory):
    remote_model_class = AmazonProductProperty
    delete_remote_instance = True

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, remote_instance=None):
        self.view = view
        super().__init__(sales_channel, local_instance, remote_product=remote_product, api=api, remote_instance=remote_instance)

    def delete_remote(self):
        listings = ListingsApi(self._get_client())
        try:
            response = listings.patch_listings_item(
                seller_id=self.sales_channel.remote_id,
                sku=self.remote_instance.remote_product.remote_sku,
                marketplace_ids=[self.view.remote_id],
                body={
                    "productType": self.remote_instance.remote_product.remote_type,
                    "requirements": "LISTING",
                    "attributes": {self.remote_instance.remote_property.main_code: None},
                },
            )
            self.update_assign_issues(getattr(response, "issues", []))
            return response
        except Exception:
            return True

    def serialize_response(self, response):
        return True
