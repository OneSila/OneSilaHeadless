from strawberry_django.optimizer import DjangoOptimizerExtension
from core.schema.core.mutations import Info, Any
from core.schema.core.mutations import type, CreateMutation


class TranslatableCreateMutation(CreateMutation):
    def __init__(self, *args, **kwargs, translation_model, translation_field, translation_model_to_model_field):
        super().__init__(*args, **kwargs)
        self.translation_model = translation_model
        self.translation_field = translation_field
        self.translation_model_to_model_field = translation_model_to_model_field

    def create(self, data: dict[str, Any], *, info: Info):
        with DjangoOptimizerExtension.disabled():

            multi_tenant_company = self.get_multi_tenant_company(info, fail_silently=False)
            language = multi_tenant_company.language

            data['multi_tenant_company'] = multi_tenant_company

            instance = super().create(data=data, info=info)
            kwargs = {
                'language': language,
                self.translation_field: data[self.translation_field],
                self.translation_model_to_model_field: instance,
                'multi_tenant_company': multi_tenant_company,
            }

            self.translation_model.objects.create(**kwargs)
            instance.refresh_from_db()
            return instance
