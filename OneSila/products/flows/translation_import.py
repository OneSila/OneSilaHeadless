from products.factories.translation_import import ProductTranslationImportFactory


class ProductTranslationImportFlow:
    def __init__(
        self,
        *,
        multi_tenant_company,
        products,
        source_channel,
        target_channel,
        language: str | None,
        override: bool,
        all_languages: bool,
        fields: list[str],
    ) -> None:
        self.multi_tenant_company = multi_tenant_company
        self.products = products
        self.source_channel = source_channel
        self.target_channel = target_channel
        self.language = language
        self.override = override
        self.all_languages = all_languages
        self.fields = fields

    def flow(self) -> None:
        factory = ProductTranslationImportFactory(
            multi_tenant_company=self.multi_tenant_company,
            products=self.products,
            source_channel=self.source_channel,
            target_channel=self.target_channel,
            language=self.language,
            override=self.override,
            all_languages=self.all_languages,
            fields=self.fields,
        )
        factory.work()
