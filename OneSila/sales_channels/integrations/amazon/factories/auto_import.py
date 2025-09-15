from properties.models import ProductProperty, Property
from sales_channels.integrations.amazon.models import (
    AmazonProductProperty,
    AmazonPropertySelectValue,
)
from django.db.models import Q


class AmazonAutoImportSelectValueFactory:
    def __init__(self, select_value: AmazonPropertySelectValue):
        self.select_value = select_value
        self.remote_property = select_value.amazon_property
        self.sales_channel = select_value.sales_channel

    def run(self):
        if not self.select_value.local_instance or not self.remote_property.local_instance:
            return

        qs = AmazonProductProperty.objects.filter(
            sales_channel=self.sales_channel,
            remote_property=self.remote_property,
            local_instance__isnull=True,
        ).filter(
            Q(remote_select_value=self.select_value) |
            Q(remote_select_values=self.select_value)
        ).select_related("remote_product", "remote_product__local_instance")

        for app in qs:
            product = app.remote_product.local_instance
            if not product:
                continue

            prop = self.remote_property.local_instance
            pp, _ = ProductProperty.objects.get_or_create(
                multi_tenant_company=product.multi_tenant_company,
                product=product,
                property=prop,
            )

            if prop.type == Property.TYPES.SELECT:
                pp.value_select = self.select_value.local_instance
                pp.save()
            elif prop.type == Property.TYPES.MULTISELECT:
                pp.save()
                if self.select_value.local_instance not in pp.value_multi_select.all():
                    pp.value_multi_select.add(self.select_value.local_instance)

            duplicates = AmazonProductProperty.objects.filter(
                remote_product=app.remote_product,
                local_instance=pp,
            ).exclude(id=app.id)

            if duplicates.exists():
                duplicates.delete()

            app.local_instance = pp
            app.save(update_fields=["local_instance"])
