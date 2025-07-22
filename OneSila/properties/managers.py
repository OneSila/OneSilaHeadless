from django.core.exceptions import ValidationError
from django.db.models import Subquery, OuterRef
from django.utils.text import slugify
from django.conf import settings
import difflib
from django.utils.translation import gettext_lazy as _
from core.managers import MultiTenantManager, MultiTenantQuerySet
from django.db import transaction, IntegrityError
from .helpers import generate_unique_internal_name


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

        property_instance = self.create(
            type='SELECT',  # we are using the text instead the constant because it created issues in the migration command
            is_public_information=True,
            is_product_type=True,
            internal_name='product_type',
            multi_tenant_company=multi_tenant_company
        )

        PropertyTranslation.objects.create(
            property=property_instance,
            language=language,
            name=name,
            multi_tenant_company=multi_tenant_company
        )
        return property_instance

    def create_brand(self, multi_tenant_company):
        from core.defaults import get_brand_name
        from .models import PropertyTranslation

        language = multi_tenant_company.language
        name = get_brand_name(language)

        property_instance = self.create(
            type='SELECT',
            is_public_information=True,
            internal_name='brand',
            non_deletable=True,
            multi_tenant_company=multi_tenant_company,
        )

        PropertyTranslation.objects.create(
            property=property_instance,
            language=language,
            name=name,
            multi_tenant_company=multi_tenant_company,
        )
        return property_instance

    def delete(self, *args, **kwargs):

        if self.filter(is_product_type=True).exists():
            raise ValidationError(_("You cannot delete the product type property."))

        if self.filter(non_deletable=True).exists():
            raise ValidationError(_("You cannot delete one or more system properties."))

        super().delete(*args, **kwargs)

    def with_translated_name(self, language_code=None):
        from .models import PropertyTranslation

        return self.annotate(
            translated_name=Subquery(
                PropertyTranslation.objects
                .filter(
                    property=OuterRef('pk'),
                    language=language_code
                )
                .order_by('name')
                .values('name')[:1]
            )
        )

    def find_duplicates(self, name, language_code=None, threshold=0.8):
        """Return properties with a name similar to the given value."""
        from .models import PropertyTranslation

        if language_code is None:
            language_code = settings.LANGUAGE_CODE

        processed_name = slugify(name).replace("-", "").lower()
        translations = PropertyTranslation.objects.filter(
            property__in=self,
            language=language_code,
        ).select_related("property")

        matched_ids = []
        for translation in translations:
            processed = slugify(translation.name).replace("-", "").lower()
            ratio = difflib.SequenceMatcher(None, processed_name, processed).ratio()
            if ratio >= threshold:
                matched_ids.append(translation.property_id)

        return self.filter(id__in=matched_ids)


class PropertyManager(MultiTenantManager):
    def get_queryset(self):
        return PropertyQuerySet(self.model, using=self._db)

    def is_public_information(self):
        return self.get_queryset().is_public_information()

    def get_product_type(self):
        return self.get_queryset().get_product_type()

    def create_product_type(self, multi_tenant_company):
        return self.get_queryset().create_product_type(multi_tenant_company)

    def create_brand(self, multi_tenant_company):
        return self.get_queryset().create_brand(multi_tenant_company)

    def check_for_duplicates(self, name, multi_tenant_company, threshold=0.8):
        qs = self.filter(multi_tenant_company=multi_tenant_company)
        return qs.find_duplicates(name, language_code=multi_tenant_company.language, threshold=threshold)

    def get_or_create(self, **kwargs):
        internal_name = kwargs.get("internal_name")
        if not internal_name and "defaults" in kwargs:
            internal_name = kwargs["defaults"].get("internal_name")

        if not internal_name:
            return super().get_or_create(**kwargs)

        base_name = slugify(internal_name).replace("-", "_")
        counter = 0

        while True:
            candidate = base_name if counter == 0 else f"{base_name}_{counter}"

            if "internal_name" in kwargs:
                kwargs["internal_name"] = candidate
            else:
                kwargs.setdefault("defaults", {})["internal_name"] = candidate

            try:
                return super().get_or_create(**kwargs)
            except IntegrityError as exc:
                if "unique_internal_name_per_company" in str(exc):
                    counter += 1
                    continue
                raise


class PropertySelectValueQuerySet(MultiTenantQuerySet):
    def delete(self, *args, **kwargs):
        if self.filter(property__is_product_type=True).exists():
            raise ValidationError(
                _("One or more property values are associated with a product type rule and cannot be removed directly. "
                  "Please delete the product type rule to remove them."))

        return super().delete(*args, **kwargs)

    def with_translated_value(self, language_code=None):
        from .models import PropertySelectValueTranslation

        return self.annotate(
            translated_value=Subquery(
                PropertySelectValueTranslation.objects
                .filter(
                    propertyselectvalue=OuterRef('pk'),
                    language=language_code,
                )
                .order_by('value')
                .values('value')[:1]
            )
        )

    def find_duplicates(self, value, property_instance, language_code=None, threshold=0.8):
        """Return property select values with a value similar to the given one."""
        from .models import PropertySelectValueTranslation

        if language_code is None:
            language_code = settings.LANGUAGE_CODE

        processed_value = slugify(value).replace("-", "").lower()
        translations = PropertySelectValueTranslation.objects.filter(
            propertyselectvalue__in=self,
            propertyselectvalue__property=property_instance,
            language=language_code,
        ).select_related("propertyselectvalue")

        matched_ids = []
        for translation in translations:
            processed = slugify(translation.value).replace("-", "").lower()
            ratio = difflib.SequenceMatcher(None, processed_value, processed).ratio()
            if ratio >= threshold:
                matched_ids.append(translation.propertyselectvalue_id)

        return self.filter(id__in=matched_ids)


class PropertySelectValueManager(MultiTenantManager):
    def get_queryset(self):
        return PropertySelectValueQuerySet(self.model, using=self._db)

    def check_for_duplicates(self, value, property_instance, multi_tenant_company, threshold=0.8):
        qs = self.filter(
            multi_tenant_company=multi_tenant_company,
            property=property_instance,
        )
        return qs.find_duplicates(
            value,
            property_instance,
            language_code=multi_tenant_company.language,
            threshold=threshold,
        )


class ProductPropertiesRuleQuerySet(MultiTenantQuerySet):
    def create_rule(self, multi_tenant_company, product_type, require_ean_code, items):
        from .models import ProductPropertiesRuleItem
        from .signals import product_properties_rule_created
        from strawberry_django.mutations.types import ParsedObject

        # we make sure it have both backend and frontend compatability
        if isinstance(product_type, ParsedObject):
            product_type = product_type.pk

        # we want to make sure we keep the sort order right but we start creating the REQUIRED_IN_CONFIGURATOR
        # to avoid errors
        items = sorted(items,
            key=lambda item: (
                0 if item.get('type') == ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR else 1,
                item.get('sort_order', 0)
            )
        )

        # Step 1: Create the rule inside an atomic transaction
        with transaction.atomic():
            rule, _ = self.get_or_create(
                product_type=product_type,
                multi_tenant_company=multi_tenant_company,
            )

            if rule.require_ean_code != require_ean_code:
                rule.require_ean_code = require_ean_code
                rule.save()

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

    def update_rule_items(self, rule, items):
        from .models import ProductPropertiesRuleItem
        from .signals import product_properties_rule_updated, product_properties_rule_configurator_updated
        from strawberry_django.mutations.types import ParsedObject

        # we want to make sure we keep the sort order right but we start creating the REQUIRED_IN_CONFIGURATOR
        # to avoid errors
        items = sorted(items,
            key=lambda item: (
                0 if item.get('type') == ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR else 1,
                item.get('sort_order', 0)
            )
        )

        with transaction.atomic():
            final_ids = []
            configurator_changed = False
            configurator_types = [ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR, ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR]

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
                    if item.get('type') in configurator_types:
                        configurator_changed = True
                else:
                    if isinstance(item_id, ParsedObject):
                        rule_item = item_id.pk
                    elif isinstance(item_id, ProductPropertiesRuleItem):
                        rule_item = item_id
                    else:
                        rule_item = ProductPropertiesRuleItem.objects.get(id=item_id)

                    if rule_item.type != item.get('type') and item.get('type') in configurator_types:
                        configurator_changed = True

                    rule_item.type = item.get('type')
                    rule_item.sort_order = item.get('sort_order', 0)
                    rule_item.save()

                final_ids.append(rule_item.id)

            # Delete items that are no longer in the updated list
            ProductPropertiesRuleItem.objects.filter(rule=rule).exclude(id__in=final_ids).delete()

            # Send the update signal
            product_properties_rule_updated.send(sender=rule.__class__, instance=rule)

            if configurator_changed:
                product_properties_rule_configurator_updated.send(sender=rule.__class__, instance=rule)

            return rule

    def delete(self, *args, **kwargs):
        from properties.models import ProductProperty
        product_type_ids = list(self.values_list('product_type_id', flat=True))

        if ProductProperty.objects.filter(value_select_id__in=product_type_ids).exists():
            raise ValidationError(
                _("One or more product type rules are currently in use by some products. "
                  "Please unassign all products from these rules before attempting deletion.")
            )

        return super().delete(*args, **kwargs)


class ProductPropertiesRuleManager(MultiTenantManager):
    def get_queryset(self):
        return ProductPropertiesRuleQuerySet(self.model, using=self._db)

    def create_rule(self, multi_tenant_company, product_type, require_ean_code, items):
        return self.get_queryset().create_rule(multi_tenant_company, product_type, require_ean_code, items)

    def update_rule_items(self, rule, items):
        return self.get_queryset().update_rule_items(rule, items)

    def delete(self, *args, **kwargs):
        return self.get_queryset().delete(*args, **kwargs)


class ProductPropertyQuerySet(MultiTenantQuerySet):
    def filter_for_configurator(self):
        from .models import ProductPropertiesRuleItem, Property, ProductPropertiesRule, \
            PropertySelectValue

        product_type_prod_props = self.filter(property__is_product_type=True)
        product_type_selects = PropertySelectValue.objects.filter(
            property__in=product_type_prod_props.values('property')
        )
        rules = ProductPropertiesRule.objects.filter(
            multi_tenant_company__in=self.values('multi_tenant_company'),
            product_type__in=product_type_selects)
        rule_items = ProductPropertiesRuleItem.objects.filter(
            rule__in=rules,
            type__in=[
                ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
                ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
            ],
            multi_tenant_company__in=self.all().values('multi_tenant_company')
        )
        properties = Property.objects.filter(
            multi_tenant_company__in=self.all().values('multi_tenant_company'),
            id__in=rule_items.values_list('property_id', flat=True)
        )
        return self.filter(property__in=properties)


class ProductPropertyManager(MultiTenantManager):
    def get_queryset(self):
        return ProductPropertyQuerySet(self.model, using=self._db)

    def filter_for_configurator(self):
        return self.get_queryset().filter_for_configurator()
