import json

import strawberry_django
from strawberry import Info
from core.schema.core.extensions import default_extensions
from sales_channels.schema.types.input import SalesChannelPartialInput
from .types.types import AiContent, AiTaskResponse, AiBulletPoints, BulletPoint, AiBulkContentResponse
from .types.input import (
    ProductAiContentInput,
    AITranslationInput,
    AIBulkTranslationInput,
    ProductAiBulletPointsInput,
    AdvancedContentGeneratorInput,
)
from core.schema.core.mutations import type, create, update, delete, List
from .types.types import BrandCustomPromptType, ChatGptProductFeedConfigType
from .types.input import (
    BrandCustomPromptInput,
    BrandCustomPromptPartialInput,
    ChatGptProductFeedConfigInput,
    ChatGptProductFeedConfigPartialInput,
)
from core.schema.core.helpers import get_multi_tenant_company
from products.models import Product
from sales_channels.models import SalesChannel
from django.core.exceptions import ValidationError


@type(name="Mutation")
class LlmMutation:
    create_brand_custom_prompt: BrandCustomPromptType = create(BrandCustomPromptInput)
    create_brand_custom_prompts: List[BrandCustomPromptType] = create(BrandCustomPromptInput)
    update_brand_custom_prompt: BrandCustomPromptType = update(BrandCustomPromptPartialInput)
    delete_brand_custom_prompt: BrandCustomPromptType = delete()
    delete_brand_custom_prompts: List[BrandCustomPromptType] = delete(is_bulk=True)
    update_chat_gpt_product_feed_config: ChatGptProductFeedConfigType = update(ChatGptProductFeedConfigPartialInput)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def generate_product_ai_content(self, instance: ProductAiContentInput, info: Info) -> AiContent:
        from llm.flows.generate_ai_content import AIGenerateContentFlow
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        language = instance.language_code
        content_type = instance.content_ai_generate_type
        product = Product.objects.get(id=instance.id.node_id, multi_tenant_company=multi_tenant_company)

        content_generator = AIGenerateContentFlow(
            product=product,
            language=language,
            content_type=content_type,
            sales_channel_type=instance.sales_channel_type,
        )
        content_generator.flow()

        return AiContent(content=content_generator.generated_content, points=content_generator.used_points)

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def generate_product_bullet_points_ai(self, instance: ProductAiBulletPointsInput, info: Info) -> AiBulletPoints:
        from llm.flows.generate_bullet_points import AIGenerateBulletPointsFlow

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        product = Product.objects.get(id=instance.id.node_id, multi_tenant_company=multi_tenant_company)

        flow = AIGenerateBulletPointsFlow(
            product=product,
            language=instance.language_code,
            return_one=instance.return_one or False,
        )
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

        sales_channel = None
        if instance.sales_channel:
            sales_channel = SalesChannel.objects.get(id=instance.sales_channel.id.node_id,
                                                     multi_tenant_company=multi_tenant_company)

        content_type = instance.product_content_type

        content_generator = AITranslateContentFlow(multi_tenant_company=multi_tenant_company,
                                                   to_translate=instance.to_translate,
                                                   from_language_code=instance.from_language_code,
                                                   to_language_code=instance.to_language_code,
                                                   product=product,
                                                   content_type=content_type,
                                                   sales_channel=sales_channel,
                                                   return_one_bullet_point=instance.return_one_bullet_point or False,
                                                   bullet_point_index=instance.bullet_point_index)
        content_generator.flow()

        return AiContent(content=content_generator.translated_content,
                         points=content_generator.used_points,
                         bullet_point_index=content_generator.bullet_point_index)

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

    @strawberry_django.mutation(
        handle_django_errors=True,
        extensions=default_extensions,
        name="advancedContentGenerator",
    )
    def advanced_content_generator(self, *, instance: AdvancedContentGeneratorInput, info: Info) -> AiBulkContentResponse:
        from llm.tasks import llm__ai_generate__run_bulk_content_flow
        from llm.flows.bulk_generate_content import BulkGenerateContentFlow

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        product_ids = [p.id.node_id for p in instance.products or []]
        sales_channel_inputs = instance.sales_channels or []
        sales_channel_languages: dict[str, list[str]] = {}
        for entry in sales_channel_inputs:
            sales_channel_id = "default"
            if entry.sales_channel:
                sales_channel_id = entry.sales_channel.id.node_id
            language = entry.language
            if not language:
                raise ValidationError("Each sales channel instruction requires a language.")
            sales_channel_languages.setdefault(sales_channel_id, [])
            if language not in sales_channel_languages[sales_channel_id]:
                sales_channel_languages[sales_channel_id].append(language)

        if not product_ids or not sales_channel_languages:
            raise ValidationError("Products and sales channels are required.")

        if instance.preview and len(product_ids) > 5:
            raise ValidationError("Preview mode supports a maximum of 20 products.")

        if instance.preview:
            flow = BulkGenerateContentFlow(
                multi_tenant_company=multi_tenant_company,
                product_ids=product_ids,
                sales_channel_languages=sales_channel_languages,
                override=instance.override or False,
                preview=True,
                additional_informations=instance.additional_informations,
                debug=instance.debug or False,
            )
            preview_payload = flow.flow()
            return AiBulkContentResponse(
                success=True,
                content=json.dumps(preview_payload),
                points=str(flow.used_points),
            )

        llm__ai_generate__run_bulk_content_flow(
            multi_tenant_company_id=multi_tenant_company.id,
            product_ids=product_ids,
            sales_channel_languages={str(key): value for key, value in sales_channel_languages.items()},
            override=instance.override or False,
            additional_informations=instance.additional_informations,
            debug=instance.debug or False,
        )

        return AiBulkContentResponse(success=True)

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
