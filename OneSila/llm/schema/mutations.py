import json

import strawberry_django
from strawberry import Info
from core.schema.core.extensions import default_extensions
from sales_channels.schema.types.input import SalesChannelPartialInput
from .types.types import AiContent, AiTaskResponse, AiBulletPoints, BulletPoint
from .types.input import (
    ProductAiContentInput,
    AITranslationInput,
    AIBulkTranslationInput,
    ProductAiBulletPointsInput,
)
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
    def generate_product_bullet_points_ai(self, instance: ProductAiBulletPointsInput, info: Info) -> AiBulletPoints:
        from llm.flows.generate_bullet_points import AIGenerateBulletPointsFlow

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        product = Product.objects.get(id=instance.id.node_id, multi_tenant_company=multi_tenant_company)

        flow = AIGenerateBulletPointsFlow(product=product, language=instance.language_code)
        flow.flow()

        bullets = [BulletPoint(text=bp) for bp in flow.generated_points]

        return AiBulletPoints(bullet_points=bullets, points=str(flow.used_points))

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
    def bulk_translate_ai_content(self, instance: AIBulkTranslationInput, info: Info) -> AiTaskResponse:
        from llm.tasks import llm__ai_translate__run_bulk_ai_translation_flow

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        product_ids = [p.id.node_id for p in instance.products or []]
        property_ids = [p.id.node_id for p in instance.properties or []]
        value_ids = [v.id.node_id for v in instance.values or []]

        llm__ai_translate__run_bulk_ai_translation_flow(
            multi_tenant_company_id=multi_tenant_company.id,
            from_language_code=instance.from_language_code,
            to_language_codes=instance.to_language_codes,
            product_ids=product_ids,
            property_ids=property_ids,
            value_ids=value_ids,
            override_translation=instance.override_translation,
        )

        return AiTaskResponse(success=True)

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
