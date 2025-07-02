from sales_channels.integrations.amazon.models.properties import (
    AmazonProperty,
    AmazonPropertySelectValue,
)

from properties.models import Property, ProductProperty

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
