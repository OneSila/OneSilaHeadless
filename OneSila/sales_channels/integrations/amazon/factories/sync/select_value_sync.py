from collections import defaultdict

from sales_channels.integrations.amazon.models import AmazonProperty
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation


class AmazonPropertySelectValuesSyncFactory:
    """Auto map remote select values with the same remote_value."""

    def __init__(self, amazon_property: AmazonProperty):
        self.amazon_property = amazon_property
        self.local_property = amazon_property.local_instance

    def run(self):
        if not self._should_run():
            return

        for vals in self._get_duplicate_value_groups():
            self._link_duplicate_values(vals)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _should_run(self) -> bool:
        """Return True if the factory should attempt any work."""
        if not self.local_property:
            return False

        if self.amazon_property.type not in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
            return False

        if self.local_property.propertyselectvalue_set.exists():
            return False

        return True

    def _get_duplicate_value_groups(self) -> list:
        """Return groups of remote select values sharing the same remote_value."""
        remote_select_values = self.amazon_property.select_values.all()
        remote_value_map: dict[str, list] = defaultdict(list)
        for val in remote_select_values:
            remote_value_map[val.remote_value].append(val)

        return [vals for vals in remote_value_map.values() if len(vals) > 1]

    def _link_duplicate_values(self, values: list) -> None:
        """Create/link a local PropertySelectValue for each provided remote value."""
        existing_psv = None
        for val in values:
            lang = val.marketplace.remote_languages.first()
            if not lang or not val.remote_name:
                # Can't create translation without a language or name
                continue

            language_code = lang.local_instance

            # Create the PropertySelectValue only once for the first valid entry
            if existing_psv is None:
                existing_psv = PropertySelectValue.objects.filter(
                    property=self.local_property,
                    propertyselectvaluetranslation__language=language_code,
                    propertyselectvaluetranslation__value__iexact=val.remote_name.strip(),
                ).first()

                if not existing_psv:
                    existing_psv = PropertySelectValue.objects.create(
                        property=self.local_property,
                        multi_tenant_company=self.amazon_property.multi_tenant_company,
                    )

            PropertySelectValueTranslation.objects.get_or_create(
                propertyselectvalue=existing_psv,
                language=language_code,
                multi_tenant_company=self.amazon_property.multi_tenant_company,
                defaults={"value": val.remote_name.strip()},
            )

            val.local_instance = existing_psv
            val.save(update_fields=["local_instance"])
