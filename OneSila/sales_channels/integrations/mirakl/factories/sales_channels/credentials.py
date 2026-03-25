from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin


class ValidateMiraklCredentialsFactory(GetMiraklAPIMixin):
    """Validate Mirakl credentials and cache account metadata."""

    def __init__(self, *, sales_channel):
        self.sales_channel = sales_channel

    def run(self):
        account_info = self.validate_credentials()
        platform_configuration = self.get_platform_configuration()
        self.sales_channel.raw_data = account_info or {}
        self.apply_platform_configuration(
            instance=self.sales_channel,
            platform_configuration=platform_configuration,
        )
        self.sales_channel.save(
            update_fields=[
                "raw_data",
                "product_import_only_on_leaf",
                "list_of_multiple_values_separator",
                "offer_prices_decimals",
                "operator_csv_delimiter",
            ]
        )
        return account_info

    def apply_platform_configuration(self, *, instance, platform_configuration):
        features = dict((platform_configuration or {}).get("features") or {})
        catalog_features = dict(features.get("catalog") or {})

        instance.product_import_only_on_leaf = bool(catalog_features.get("product_import_only_on_leaf", False))
        instance.list_of_multiple_values_separator = str(catalog_features.get("list_of_multiple_values_separator") or "").strip()

        offer_prices_decimals = str(features.get("offer_prices_decimals") or "").strip()
        try:
            instance.offer_prices_decimals = int(offer_prices_decimals) if offer_prices_decimals else None
        except (TypeError, ValueError):
            instance.offer_prices_decimals = None

        operator_csv_delimiter = str(features.get("operator_csv_delimiter") or "").strip()
        valid_delimiters = {
            choice[0]
            for choice in getattr(instance, "CSV_DELIMITER_CHOICES", [])
        }
        instance.operator_csv_delimiter = operator_csv_delimiter if operator_csv_delimiter in valid_delimiters else ""
