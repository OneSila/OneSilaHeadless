from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation

class CreateProductMutation(CreateMutation):
    def create(self, data: dict[str, Any], *, info: Info):
        from products.models import ProductTranslation

        with DjangoOptimizerExtension.disabled():

            multi_tenant_compane = self.get_multi_tenant_company(info)
            language = multi_tenant_compane.language

            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            data['multi_tenant_company'] = multi_tenant_company

            product = super().create(data=data, info=info)

            ProductTranslation.objects.create(
                product=product,
                language=language,
                name=data['name'],
                multi_tenant_company=multi_tenant_company,
            )
            product.refresh_from_db()
            return product