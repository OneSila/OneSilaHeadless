import time
from decimal import Decimal
import openai
from django.core.exceptions import ValidationError
from core.managers import MultiTenantQuerySet, MultiTenantManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class AiPointContentGenerateProcessQuerySet(MultiTenantQuerySet):
    def create_from_prompt(self, prompt, product, images=None, language="en"):
        """
        Creates an AiPointContentGenerateProccess from a given prompt (and optional image)
        for a product.
        Raises a ValidationError if the company's AI points are already negative.
        """
        from .models import AiPointTransaction  # Ensure correct import

        company = product.multi_tenant_company

        # Check if the company already has negative AI points.
        if company.ai_points < 0:
            raise ValidationError(_("Insufficient AI points. Please purchase more."))

        # Initialize OpenAI client using API key from settings.
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        instructions_text = (
            f"You are a professional product description writer specializing in SEO-optimized, "
            f"user-friendly content. Based on the provided prompt"
            f"{' and image' if images else ''}, generate a clear, engaging, and well-structured "
            f"HTML-formatted description. Use appropriate HTML elements (such as headings, paragraphs, and bullet lists) "
            f"to organize the content, include relevant keywords naturally, and ensure the description is written in {language.upper()}. "
            f"Make sure the text is concise yet informative, and tailored to highlight the product's unique features."
            f'Instead of <ul> please use <ol> with <li data-list="bullet"></li>' # needed for the frontend
        )

        start_time = time.time()
        if images:
            # response = client.responses.create(
            #     model="gpt-4o-mini",
            #     instructions=instructions_text,
            #     max_output_tokens=500,
            #     input=[
            #         {
            #             "role": "user",
            #             "content": [
            #                 {"type": "input_text", "text": prompt},
            #                 {"type": "input_image", "image_url": f"data:image/png;base64,{images}"}
            #             ]
            #         }
            #     ],
            #     metadata={"has_image": "yes"}
            # )

            image_inputs = [{"type": "input_image", "image_url": url} for url in images]
            response = client.responses.create(
                model="gpt-4o-mini",
                instructions=instructions_text,
                max_output_tokens=500,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            *image_inputs
                        ]
                    }
                ],
                metadata={"has_image": "yes"}
            )
            result_text = response.output_text
            # Use rates for gpt-4o-mini:
            prompt_rate = Decimal("0.150")      # dollars per 1M input tokens
            completion_rate = Decimal("0.600")  # dollars per 1M output tokens
        else:
            response = client.responses.create(
                model="gpt-4o",
                max_output_tokens=500,
                instructions=instructions_text,
                input=prompt
            )
            result_text = response.output_text
            # Use rates for gpt-4o:
            prompt_rate = Decimal("2.50")       # dollars per 1M input tokens
            completion_rate = Decimal("10.00")  # dollars per 1M output tokens

        end_time = time.time()
        result_time = end_time - start_time

        usage = response.usage
        prompt_tokens = usage.input_tokens
        completion_tokens = usage.output_tokens

        cost_prompt = (Decimal(prompt_tokens) / Decimal(1e6)) * prompt_rate
        cost_completion = (Decimal(completion_tokens) / Decimal(1e6)) * completion_rate
        total_cost = cost_prompt + cost_completion

        const_price = Decimal(getattr(settings, "AI_POINT_PRICE", "0.1"))
        multiplier = Decimal(getattr(settings, "AI_POINT_MULTIPLIER", "10"))
        points_cost = max(1, int(round(total_cost / const_price * multiplier)))

        result_text = result_text.replace('```html', '').replace("```", '')

        transaction = AiPointTransaction.objects.create(
            points=points_cost,
            transaction_type=AiPointTransaction.SUBTRACT,
            multi_tenant_company=company,
        )

        return self.create(
            product=product,
            transaction=transaction,
            prompt=prompt,
            result=result_text,
            result_time=result_time,
            cost=total_cost,
            multi_tenant_company=company,
        )


class AiPointContentGenerateProcessManager(MultiTenantManager):
    def get_queryset(self):
        return AiPointContentGenerateProcessQuerySet(self.model, using=self._db)

    def create_from_prompt(self, prompt, product, images=None, language="en"):
        return self.get_queryset().create_from_prompt(prompt, product, images, language)
