from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonProductType,
    AmazonPublicDefinition,
    AmazonPropertySelectValue,
)
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from properties.models import Property, ProductProperty
import json
import re
from properties.models import ProductProperty

TOKEN_RE = re.compile(r"%([a-z_]+):([^%]+)%")


class AmazonRemoteValueMixin:
    """Utility methods to obtain remote values for product properties."""

    def _get_select_remote_value(self, prop_instance: ProductProperty, remote_property: AmazonProperty):

        # @TODO: MAKE SURE THE VALUES ARE FILTERED BY THE RIGHT LANGUAGE
        if prop_instance.property.type == Property.TYPES.MULTISELECT:
            values = prop_instance.value_multi_select.all()
        else:
            values = [prop_instance.value_select] if prop_instance.value_select else []

        remote_values = []
        for val in values:
            if not val:
                continue
            remote_val = AmazonPropertySelectValue.objects.filter(
                amazon_property=remote_property,
                local_instance=val,
                marketplace=self.view,
            ).first()
            if not remote_val:
                if not remote_property.allows_unmapped_values:
                    raise ValueError(
                        f"Value {val.value} not mapped for {remote_property.code}"
                    )
                remote_values.append(val.value)
            else:
                remote_values.append(remote_val.remote_value)
        if prop_instance.property.type == Property.TYPES.SELECT:
            return remote_values[0] if remote_values else None
        return remote_values

    def get_remote_value_for_property(self, prop_instance: ProductProperty, remote_property: AmazonProperty):
        value = prop_instance.get_value()
        ptype = prop_instance.property.type
        if ptype in [Property.TYPES.INT, Property.TYPES.FLOAT]:
            return value
        if ptype == Property.TYPES.BOOLEAN:
            return True if value in [True, "true", "1", 1] else False
        if ptype in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
            return self._get_select_remote_value(prop_instance, remote_property)

        # @TODO: MAKE SURE THE TEXT / DESCRIPTION ARE IN THE RIGHT LANGUAGE OF THE MARKETPLACE
        if ptype in [Property.TYPES.TEXT, Property.TYPES.DESCRIPTION]:
            return value
        if ptype == Property.TYPES.DATE:
            return value.isoformat() if value else None
        if ptype == Property.TYPES.DATETIME:
            return value.isoformat() if value else None
        return value


class AmazonProductPropertyBaseMixin(GetAmazonAPIMixin, AmazonRemoteValueMixin):
    """Common helpers for Amazon product property factories."""

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
                self.remote_property = AmazonProperty.objects.get(
                    sales_channel=self.sales_channel, code=code
                )
                local_prop = self.remote_property.local_instance
                prop_instance = ProductProperty.objects.get(
                    product=product, property=local_prop
                )
                return self.get_remote_value_for_property(prop_instance, self.remote_property)
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

        if not product_type:
            raise ValueError("Product has no product type mapped")

        if not self.sales_channel.listing_owner:
            allowed_properties = product_type.listing_offer_required_properties.get(self.view.api_region_code, [])
            if main_code not in allowed_properties:
                return product_type, {}

        public_def = self._get_public_definition(product_type, main_code)
        if not public_def.usage_definition:
            raise ValueError("Missing usage definition for property")
        usage = json.loads(public_def.usage_definition)

        payload = self._replace_tokens(usage, self.local_instance.product)
        return product_type, payload

    # ------------------------------------------------------------------
    def preflight_check(self):
        if not super().preflight_check():
            return False
        try:
            self._get_remote_property()
        except AmazonProperty.DoesNotExist:
            return False

        return True

    def create_body(self):
        self.remote_rule, payload = self.build_payload()

        self.remote_value = json.dumps(payload)

        if self.get_value_only:

            if hasattr(self, 'remote_instance') and self.remote_instance:
                self.remote_instance.remote_value = self.remote_value
                self.remote_instance.save()

            return None

        body = {
            "productType": self.remote_rule.product_type_code,
            "requirements": "LISTING",
            "attributes": payload,
        }
        self.value = body
        return body

    def preflight_process(self):
        pass

    def set_remote_id(self, response_data):
        # the product properties have na remote id
        pass

