from sales_channels.integrations.mirakl.models import (
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklPublicDefinition,
)


class MiraklPublicDefinitionSyncFactory:
    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel

    def run(self) -> int:
        synced = 0
        queryset = MiraklProperty.objects.filter(
            sales_channel=self.sales_channel,
            representation_type_decided=False,
        ).order_by("id")

        for remote_property in queryset.iterator():
            public_definition, _ = MiraklPublicDefinition.objects.get_or_create(
                hostname=self.sales_channel.hostname,
                property_code=remote_property.code,
            )
            public_definition.representation_type = remote_property.representation_type
            public_definition.language = remote_property.language
            public_definition.default_value = remote_property.default_value or ""
            yes_value, no_value = self._resolve_boolean_values(remote_property=remote_property)
            public_definition.yes_text_value = yes_value
            public_definition.no_text_value = no_value
            public_definition.save()

            remote_property.representation_type_decided = True
            remote_property.save(update_fields=["representation_type_decided"])
            synced += 1

        return synced

    def _resolve_boolean_values(self, *, remote_property) -> tuple[str, str]:
        yes_value = remote_property.yes_text_value or ""
        no_value = remote_property.no_text_value or ""

        if remote_property.type == "SELECT":
            yes_option = (
                MiraklPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_property=remote_property,
                    bool_value=True,
                )
                .order_by("id")
                .first()
            )
            no_option = (
                MiraklPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_property=remote_property,
                    bool_value=False,
                )
                .order_by("id")
                .first()
            )
            if yes_option is not None:
                yes_value = yes_option.value or yes_option.code or yes_value
            if no_option is not None:
                no_value = no_option.value or no_option.code or no_value

        return str(yes_value or ""), str(no_value or "")
