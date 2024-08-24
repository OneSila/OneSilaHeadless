from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from core.managers import MultiTenantManager, MultiTenantQuerySet
from django.db import transaction


class PropertyQuerySet(MultiTenantQuerySet):
    def is_public_information(self):
        return self.filter(is_public_information=True)

    def get_product_type(self):
        return self.filter(is_product_type=True)

    def create_product_type(self, multi_tenant_company):
        from core.defaults import get_product_type_name
        from .models import PropertyTranslation

        language = multi_tenant_company.language
        name = get_product_type_name(language)
        internal_name = slugify(name).replace('-', '_')

        property_instance = self.create(
            type='SELECT',  # we are using the text instead the constant because it created issues in the migration command
            is_public_information=True,
            is_product_type=True,
            internal_name=internal_name,
            multi_tenant_company=multi_tenant_company
        )

        PropertyTranslation.objects.create(
            property=property_instance,
            language=language,
            name=name,
            multi_tenant_company=multi_tenant_company
        )
        return property_instance

    def delete(self, *args, **kwargs):
        if self.filter(is_product_type=True).exists():
            raise ValidationError(_("You cannot delete a Property with is_product_type=True."))
        super().delete(*args, **kwargs)


class PropertyManager(MultiTenantManager):
    def get_queryset(self):
        return PropertyQuerySet(self.model, using=self._db)

    def is_public_information(self):
        return self.get_queryset().is_public_information()

    def get_product_type(self):
        return self.get_queryset().get_product_type()

    def create_product_type(self, multi_tenant_company):
        return self.get_queryset().create_product_type(multi_tenant_company)


class ProductPropertiesRuleQuerySet(MultiTenantQuerySet):
    def create_rule(self, multi_tenant_company, product_type, items):
        from .models import ProductPropertiesRuleItem
        from .signals import product_properties_rule_created
        from strawberry_django.mutations.types import ParsedObject

        # we make sure it have both backend and frontend compatability
        if isinstance(product_type, ParsedObject):
            product_type = product_type.pk

        # Step 1: Create the rule inside an atomic transaction
        with transaction.atomic():
            rule, _ = self.get_or_create(
                product_type=product_type,
                multi_tenant_company=multi_tenant_company
            )

            for item in items:
                property_instance = item.get('property')

                if isinstance(property_instance, ParsedObject):
                    property_instance = property_instance.pk

                ProductPropertiesRuleItem.objects.create(
                    multi_tenant_company=multi_tenant_company,
                    rule=rule,
                    property=property_instance,
                    type=item.get('type'),
                    sort_order=item.get('sort_order', 0)
                )

            product_properties_rule_created.send(sender=rule.__class__, instance=rule)

            return rule

    def update_rule(self, rule, items):
        from .models import ProductPropertiesRuleItem
        from .signals import product_properties_rule_updated
        from strawberry_django.mutations.types import ParsedObject

        with transaction.atomic():
            final_ids = []

            for item in items:
                item_id = item.get('id')

                property_instance = item.get('property')
                if isinstance(property_instance, ParsedObject):
                    property_instance = property_instance.pk

                if item_id is None:
                    # Create a new item
                    rule_item = ProductPropertiesRuleItem.objects.create(
                        multi_tenant_company=rule.multi_tenant_company,
                        rule=rule,
                        property=property_instance,
                        type=item.get('type'),
                        sort_order=item.get('sort_order', 0)
                    )
                else:
                    if isinstance(item_id, ParsedObject):
                        rule_item = item_id.pk
                    elif isinstance(item_id, ProductPropertiesRuleItem):
                        rule_item = item_id
                    else:
                        rule_item = ProductPropertiesRuleItem.objects.get(id=item_id)

                    rule_item.type = item.get('type')
                    rule_item.sort_order = item.get('sort_order', 0)
                    rule_item.save()

                final_ids.append(rule_item.id)

            # Delete items that are no longer in the updated list
            ProductPropertiesRuleItem.objects.filter(rule=rule).exclude(id__in=final_ids).delete()

            # Send the update signal
            product_properties_rule_updated.send(sender=rule.__class__, instance=rule)

            return rule


class ProductPropertiesRuleManager(MultiTenantManager):
    def get_queryset(self):
        return ProductPropertiesRuleQuerySet(self.model, using=self._db)

    def create_rule(self, multi_tenant_company, product_type, items):
        return self.get_queryset().create_rule(multi_tenant_company, product_type, items)

    def update_rule(self, rule, items):
        return self.get_queryset().update_rule(rule, items)
