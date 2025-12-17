from django.core.exceptions import ValidationError
from django.db.models import Subquery, OuterRef, Value, CharField, Exists, Min
from django.db.models.functions import Coalesce
from django.utils.text import slugify
from django.conf import settings
import difflib
from django.utils.translation import gettext_lazy as _
from core.managers import MultiTenantManager, MultiTenantQuerySet
from django.db import transaction, IntegrityError
from .helpers import generate_unique_internal_name, _is_code_like, _norm_code, _tokens


class PropertyQuerySet(MultiTenantQuerySet):
    def with_product_usage(self, *, multi_tenant_company_id: int):
        from .models import ProductProperty

        usage_qs = ProductProperty._base_manager.filter(
            multi_tenant_company_id=multi_tenant_company_id,
            property_id=OuterRef("pk"),
        ).only("pk")

        return self.annotate(has_usage=Exists(usage_qs))

    def used_in_products(self, *, multi_tenant_company_id: int, used: bool):
        return (
            self.filter(multi_tenant_company_id=multi_tenant_company_id)
            .with_product_usage(multi_tenant_company_id=multi_tenant_company_id)
            .filter(has_usage=used)
        )

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

        language_field = language_code if language_code is not None else OuterRef('multi_tenant_company__language')
        name_in_language = PropertyTranslation.objects.filter(
            property=OuterRef('pk'),
            language=language_field,
        ).values('name')[:1]

        any_name = PropertyTranslation.objects.filter(
            property=OuterRef('pk'),
        ).values('name')[:1]

        return self.annotate(
            translated_name=Coalesce(
                Subquery(name_in_language, output_field=CharField()),
                Subquery(any_name, output_field=CharField()),
                Value('No Name Set'),
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

        matched_ids = set()
        for translation in translations:
            processed = slugify(translation.name).replace("-", "").lower()
            ratio = difflib.SequenceMatcher(None, processed_name, processed).ratio()
            if ratio >= threshold:
                matched_ids.add(translation.property_id)

        return self.filter(id__in=matched_ids).order_by('id').distinct('id')


class PropertyManager(MultiTenantManager):
    def get_queryset(self):
        return PropertyQuerySet(self.model, using=self._db)

    def used_in_products(self, *, multi_tenant_company_id: int, used: bool):
        return self.get_queryset().used_in_products(
            multi_tenant_company_id=multi_tenant_company_id,
            used=used,
        )

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
    def with_product_usage(self, *, multi_tenant_company_id: int):
        from .models import ProductProperty

        usage_select_qs = ProductProperty._base_manager.filter(
            multi_tenant_company_id=multi_tenant_company_id,
            value_select_id=OuterRef("pk"),
        ).only("pk")

        exists_expr = Exists(usage_select_qs)

        m2m_field = ProductProperty._meta.get_field("value_multi_select")
        through = m2m_field.remote_field.through
        src_fk_name = m2m_field.m2m_field_name()
        tgt_fk_name = m2m_field.m2m_reverse_field_name()

        usage_multi_qs = through._base_manager.filter(
            **{
                f"{src_fk_name}__multi_tenant_company_id": multi_tenant_company_id,
                f"{tgt_fk_name}_id": OuterRef("pk"),
            }
        ).only("pk")

        exists_expr = exists_expr | Exists(usage_multi_qs)

        return self.annotate(has_usage=exists_expr)

    def used_in_products(self, *, multi_tenant_company_id: int, used: bool):
        return (
            self.filter(multi_tenant_company_id=multi_tenant_company_id)
            .with_product_usage(multi_tenant_company_id=multi_tenant_company_id)
            .filter(has_usage=used)
        )

    def delete(self, *args, **kwargs):
        if self.filter(property__is_product_type=True).exists():
            raise ValidationError(
                _("One or more property values are associated with a product type rule and cannot be removed directly. "
                  "Please delete the product type rule to remove them."))

        return super().delete(*args, **kwargs)

    def with_translated_value(self, language_code=None):
        from .models import PropertySelectValueTranslation

        language_field = language_code if language_code is not None else OuterRef('property__multi_tenant_company__language')
        value_in_language = PropertySelectValueTranslation.objects.filter(
            propertyselectvalue=OuterRef('pk'),
            language=language_field,
        ).values('value')[:1]

        any_value = PropertySelectValueTranslation.objects.filter(
            propertyselectvalue=OuterRef('pk'),
        ).values('value')[:1]

        return self.annotate(
            translated_value=Coalesce(
                Subquery(value_in_language, output_field=CharField()),
                Subquery(any_value, output_field=CharField()),
                Value('No Value Set'),
            )
        )

    def find_duplicates(self, value, property_instance, language_code=None, threshold=0.88):
        """
        Return property select values similar to `value` within the same property.

        Rules:
          - If EITHER side looks code-like (any token has letters+digits), require exact match
            after collapsing non-alnum (prevents ath_s700bt ~ ath_s200bt).
          - Otherwise (labels), require EXACT equality of numeric token sets; only then:
              * match if token sets are equal (order/sep-insensitive), or
              * fall back to fuzzy on TEXT tokens only (numbers already matched).
        """
        from .models import PropertySelectValueTranslation

        if language_code is None:
            language_code = settings.LANGUAGE_CODE

        probe_is_code = _is_code_like(value)
        probe_code_key = _norm_code(value) if probe_is_code else None

        # Precompute probe tokens & split into numeric/text
        probe_all_tokens = _tokens(value)
        probe_num_set = {t for t in probe_all_tokens if t.isdigit()}
        probe_text_set = set(t for t in probe_all_tokens if not t.isdigit())
        probe_tokens_sorted = sorted(probe_text_set | probe_num_set)  # for exact set compare when needed
        probe_text_key = " ".join(sorted(probe_text_set))  # for fuzzy on text only

        translations = (
            PropertySelectValueTranslation.objects
            .filter(
                propertyselectvalue__in=self,
                propertyselectvalue__property=property_instance,
                language=language_code,
            )
            .select_related("propertyselectvalue")
        )

        matched_ids = set()

        for t in translations:
            raw = t.value or ""
            cand_is_code = _is_code_like(raw)

            if probe_is_code or cand_is_code:
                # CODE COMPARATOR: strict equality after collapsing
                if probe_code_key and probe_code_key == _norm_code(raw):
                    matched_ids.add(t.propertyselectvalue_id)
                continue

            # LABEL COMPARATOR
            cand_all_tokens = _tokens(raw)
            cand_num_set = {x for x in cand_all_tokens if x.isdigit()}
            cand_text_set = set(x for x in cand_all_tokens if not x.isdigit())

            # 1) Different numeric tokens => NOT a duplicate (e.g., 50 vs 60 Hertz)
            if probe_num_set != cand_num_set:
                continue

            # 2) Exact token set equality (numbers + text), order/sep-insensitive
            cand_tokens_sorted = sorted(cand_text_set | cand_num_set)
            if probe_tokens_sorted == cand_tokens_sorted:
                matched_ids.add(t.propertyselectvalue_id)
                continue

            # 3) Conservative fuzzy on TEXT ONLY (numbers already proven equal)
            cand_text_key = " ".join(sorted(cand_text_set))
            if difflib.SequenceMatcher(None, probe_text_key, cand_text_key).ratio() >= threshold:
                matched_ids.add(t.propertyselectvalue_id)

        return self.filter(id__in=matched_ids).order_by('id').distinct('id')

    def merge(self, target):
        from .models import PropertySelectValue
        from .models import ProductProperty

        if isinstance(target, (int, str)):
            target = PropertySelectValue.objects.get(pk=target)

        sources = self.exclude(pk=target.pk)

        if sources.exclude(property_id=target.property_id).exists():
            raise ValidationError(_("Property select values must belong to the same property."))

        with transaction.atomic():
            source_ids = list(sources.values_list("pk", flat=True))

            if source_ids:
                ProductProperty._base_manager.filter(
                    value_select_id__in=source_ids,
                ).update(value_select_id=target.pk)

                m2m_field = ProductProperty._meta.get_field("value_multi_select")
                through = m2m_field.remote_field.through
                through_pk = through._meta.pk.name

                through_manager = through._base_manager

                src_fk_name = m2m_field.m2m_field_name()
                tgt_fk_name = m2m_field.m2m_reverse_field_name()
                src_fk_id = f"{src_fk_name}_id"
                tgt_fk_id = f"{tgt_fk_name}_id"

                # We must ensure there are no lingering m2m references to source ids before deleting them.
                # Avoid tenant-scoped filtering here: the through table doesn't carry tenant info, and
                # legacy/nullable product_property.multi_tenant_company would otherwise leave references behind.
                product_properties_with_target = through_manager.filter(
                    **{tgt_fk_id: target.pk}
                ).values_list(src_fk_id, flat=True).distinct()

                # If a product property already has the target value, drop any source rows for it.
                if product_properties_with_target:
                    through_manager.filter(
                        **{
                            tgt_fk_id + "__in": source_ids,
                            src_fk_id + "__in": product_properties_with_target,
                        }
                    ).delete()

                # For the remaining product properties, collapse multiple source rows down to a single row,
                # then repoint that row to the target.
                remaining_through_qs = through_manager.filter(
                    **{tgt_fk_id + "__in": source_ids}
                ).exclude(**{src_fk_id + "__in": product_properties_with_target})
                keeper_ids = list(
                    remaining_through_qs.values(src_fk_id).annotate(keep_pk=Min(through_pk)).values_list("keep_pk", flat=True)
                )
                if keeper_ids:
                    through_manager.filter(**{f"{through_pk}__in": keeper_ids}).update(**{tgt_fk_id: target.pk})

                # Delete any leftover source rows (e.g. duplicates within the same product property).
                through_manager.filter(**{tgt_fk_id + "__in": source_ids}).delete()

            for source in sources:
                for relation in PropertySelectValue._meta.related_objects:
                    if relation.related_model.__name__ == "PropertySelectValueTranslation":
                        continue
                    if relation.related_model.__name__ == "ProductProperty":
                        continue
                    if relation.one_to_many or relation.one_to_one:
                        qs = relation.related_model._base_manager.filter(
                            **{relation.field.name: source}
                        )
                        for obj in qs:
                            setattr(obj, relation.field.name, target)
                            try:
                                with transaction.atomic():
                                    obj.save()
                            except IntegrityError:
                                obj.delete()
                    elif relation.many_to_many:
                        through = relation.through._base_manager
                        source_field = relation.field.m2m_reverse_field_name()
                        for through_obj in through.filter(**{source_field: source.pk}):
                            setattr(through_obj, source_field, target.pk)
                            try:
                                with transaction.atomic():
                                    through_obj.save()
                            except IntegrityError:
                                through_obj.delete()
                source.delete(force_delete=True)
            return target


class PropertySelectValueManager(MultiTenantManager):
    def get_queryset(self):
        return PropertySelectValueQuerySet(self.model, using=self._db)

    def used_in_products(self, *, multi_tenant_company_id: int, used: bool):
        return self.get_queryset().used_in_products(
            multi_tenant_company_id=multi_tenant_company_id,
            used=used,
        )

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

    def merge(self, sources, target):
        if hasattr(sources, "merge"):
            return sources.merge(target)
        ids = [s if isinstance(s, (int, str)) else s.pk for s in sources]
        return self.filter(id__in=ids).merge(target)


class ProductPropertiesRuleQuerySet(MultiTenantQuerySet):
    def create_rule(self, multi_tenant_company, product_type, require_ean_code, items, sales_channel=None):
        from .models import ProductPropertiesRuleItem
        from .signals import product_properties_rule_created
        from strawberry_django.mutations.types import ParsedObject

        # we make sure it have both backend and frontend compatability
        if isinstance(product_type, ParsedObject):
            product_type = product_type.pk

        if isinstance(sales_channel, ParsedObject):
            sales_channel = sales_channel.pk
        elif hasattr(sales_channel, "pk"):
            sales_channel = sales_channel.pk

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
                sales_channel=sales_channel,
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

    def create_rule(self, multi_tenant_company, product_type, require_ean_code, items, sales_channel=None):
        return self.get_queryset().create_rule(
            multi_tenant_company,
            product_type,
            require_ean_code,
            items,
            sales_channel=sales_channel,
        )

    def update_rule_items(self, rule, items):
        return self.get_queryset().update_rule_items(rule, items)

    def delete(self, *args, **kwargs):
        return self.get_queryset().delete(*args, **kwargs)


class ProductPropertyQuerySet(MultiTenantQuerySet):
    def filter_for_configurator(self, *, sales_channel=None):
        from .models import ProductPropertiesRuleItem, Property, ProductPropertiesRule, \
            PropertySelectValue

        # Narrow down to the product-type properties for the current queryset.
        product_type_prod_props = self.filter(property__is_product_type=True)
        product_type_selects = PropertySelectValue.objects.filter(
            property__in=product_type_prod_props.values('property')
        )

        rules_qs = ProductPropertiesRule.objects.filter(
            multi_tenant_company__in=self.values('multi_tenant_company'),
            product_type__in=product_type_selects,
        )

        if sales_channel is not None:
            channel_rules_qs = rules_qs.filter(sales_channel=sales_channel)
            if channel_rules_qs.exists():
                rules_qs = channel_rules_qs
            else:
                rules_qs = rules_qs.filter(sales_channel__isnull=True)
        else:
            rules_qs = rules_qs.filter(sales_channel__isnull=True)

        rule_items = ProductPropertiesRuleItem.objects.filter(
            rule__in=rules_qs,
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

    def filter_for_configurator(self, *, sales_channel=None):
        return self.get_queryset().filter_for_configurator(sales_channel=sales_channel)
