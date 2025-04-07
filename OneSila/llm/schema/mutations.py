import json

import strawberry_django
from strawberry import Info
from core.schema.core.extensions import default_extensions
from sales_channels.schema.types.input import SalesChannelPartialInput
from .types.types import AiContent
from .types.input import ProductAiContentInput, AITranslationInput
from core.schema.core.mutations import type
from core.schema.core.helpers import get_multi_tenant_company
from products.models import Product

@type(name="Mutation")
class LlmMutation:

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def generate_product_ai_content(self, instance: ProductAiContentInput, info: Info) -> AiContent:
        from llm.flows.generate_ai_content import AIGenerateContentFlow
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        language = instance.language_code
        content_type = instance.content_ai_generate_type
        product = Product.objects.get(id=instance.id.node_id, multi_tenant_company=multi_tenant_company)

        content_generator = AIGenerateContentFlow(product=product, language=language, content_type=content_type)
        content_generator.flow()

        return AiContent(content=content_generator.generated_content, points=content_generator.used_points)


    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def generate_ai_translation(self, instance: AITranslationInput, info: Info) -> AiContent:
        from llm.flows.translate_ai_content import AITranslateContentFlow

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        product = None
        if instance.product:
            product = Product.objects.get(id=instance.product.id.node_id, multi_tenant_company=multi_tenant_company)

        content_type = instance.product_content_type

        content_generator = AITranslateContentFlow(multi_tenant_company=multi_tenant_company,
                                                   to_translate=instance.to_translate,
                                                   from_language_code=instance.from_language_code,
                                                   to_language_code=instance.to_language_code,
                                                   product=product,
                                                   content_type=content_type)
        content_generator.flow()

        return AiContent(content=content_generator.translated_content, points=content_generator.used_points)


    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def detect_remote_valid_properties(self, instance: SalesChannelPartialInput, info: Info) -> AiContent:
        from sales_channels.models import SalesChannel
        from llm.flows.detect_remote_attributes import DetectRealAttributesFlow

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        sales_channel = SalesChannel.objects.get(id=instance.id.node_id, multi_tenant_company=multi_tenant_company)
        flow = DetectRealAttributesFlow(sales_channel=sales_channel)
        selected = flow.flow()

        return AiContent(
            content=json.dumps(selected),
            points=str(flow.used_points)
        )