from core.schema.core.mutations import CreateMutation
from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any

class CreatePropertyMutation(CreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        from properties.models import PropertyTranslation

        with DjangoOptimizerExtension.disabled():

            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            language = multi_tenant_company.language

            data['multi_tenant_company'] = multi_tenant_company

            property = super().create(data=data, info=info)

            PropertyTranslation.objects.create(
                property=property,
                language=language,
                name=data['name'],
                multi_tenant_company=multi_tenant_company,
            )
            property.refresh_from_db()

            return property

class CreatePropertySelectValueMutation(CreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        from properties.models import PropertySelectValueTranslation

        with DjangoOptimizerExtension.disabled():

            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            language = multi_tenant_company.language

            data['multi_tenant_company'] = multi_tenant_company

            property_select_value = super().create(data=data, info=info)

            PropertySelectValueTranslation.objects.create(
                propertyselectvalue=property_select_value,
                language=language,
                value=data['value'],
                multi_tenant_company=multi_tenant_company,
            )
            property_select_value.refresh_from_db()

            return property_select_value