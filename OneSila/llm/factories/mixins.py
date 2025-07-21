import time
from decimal import Decimal

import openai
from django.conf import settings
import replicate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from billing.models import AiPointTransaction
from llm.models import AiGenerateProcess, AiTranslationProcess, AiImportProcess
from media.models import MediaProductThrough, Media
from products.models import ProductTranslation
from properties.helpers import get_product_properties_dict

import logging
logger = logging.getLogger(__name__)


class OpenAIMixin:
    def __init__(self):
        self.openai = openai.Client(api_key=settings.OPENAI_API_KEY)


class CreateTransactionMixin:

    def _create_transaction(self):
        self.transaction = AiPointTransaction.objects.create(
            points=self.points_cost,
            transaction_type=AiPointTransaction.SUBTRACT,
            multi_tenant_company=self.multi_tenant_company)
        return self.transaction

    def _create_ai_generate_process(self):
        self.ai_process = AiGenerateProcess.objects.create(
            product=self.product,
            transaction=self.transaction,
            prompt=self.prompt,
            result=self.text_response,
            result_time=self.result_time,
            cost=self.total_cost,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cached_tokens=self.cached_tokens,
            multi_tenant_company=self.multi_tenant_company)

        return self.ai_process

    def _create_ai_translate_process(self):
        self.ai_process = AiTranslationProcess.objects.create(
            to_translate=self.to_translate,
            prompt=self.prompt,
            from_language_code=self.from_language_code,
            to_language_code=self.to_language_code,
            transaction=self.transaction,
            result=self.text_response,
            result_time=self.result_time,
            cost=self.total_cost,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cached_tokens=self.cached_tokens,
            multi_tenant_company=self.multi_tenant_company)

        return self.ai_process

    def _create_ai_import_process(self):
        self.ai_process = AiImportProcess.objects.create(
            transaction=self.transaction,
            prompt=self.prompt,
            result=self.text_response,
            result_time=self.result_time,
            cost=self.total_cost,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cached_tokens=self.cached_tokens,
            multi_tenant_company=self.multi_tenant_company,
            type=self.import_type
        )
        return self.ai_process


class CalculateCostMixin:

    # prices are USD per 1M tokens
    COSTS = {
        "gpt-4o": {
            "input": Decimal("2.50"),
            "output": Decimal("10.00"),
            "cached": Decimal("1.25"),
        },
        "gpt-4o-mini": {
            "input": Decimal("0.150"),
            "output": Decimal("0.600"),
            "cached": Decimal("0.075"),
        }
    }

    def calculate_cost(self, response):
        usage = response.usage
        cost = self.COSTS.get(self.model, "gpt-4o-mini")

        self.input_tokens = usage.input_tokens
        self.output_tokens = usage.output_tokens
        self.cached_tokens = usage.input_tokens_details.cached_tokens

        cost_input = (Decimal(self.input_tokens) / Decimal(1e6)) * cost['input']
        cost_output = (Decimal(self.output_tokens) / Decimal(1e6)) * cost['output']
        cost_cached = (Decimal(self.cached_tokens) / Decimal(1e6)) * cost['cached']
        self.total_cost = cost_input + cost_output + cost_cached

        const_price = Decimal(getattr(settings, "AI_POINT_PRICE", "0.1"))
        multiplier = Decimal(getattr(settings, "AI_POINT_MULTIPLIER", "10"))

        self.points_cost = max(1, int(round(self.total_cost / const_price * multiplier)))


class AskGPTMixin(OpenAIMixin):
    model = 'gpt-4o-mini'
    temperature = 0.7
    max_tokens = 2000

    def ask_gpt(self):
        logger.debug(f"About to ask_gpt")

        if not hasattr(self, 'images'):
            self.images = []

        image_inputs = [{"type": "input_image", "image_url": url} for url in self.images]
        start_time = time.time()
        response = self.openai.responses.create(
            model="gpt-4o-mini",
            instructions=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": self.prompt},
                        *image_inputs
                    ]
                }
            ]
        )

        end_time = time.time()
        self.result_time = end_time - start_time

        return response

    def get_text_response(self, response):
        return response.output_text.strip()

    def generate_response(self):
        return self.get_text_response(self.ask_gpt())


class AskDalleMixin(OpenAIMixin):
    model = 'dall-e-3'
    size = "1792x1024"
    max_tokens = 2000
    quality = "standard"
    n = 1

    def __init__(self):
        self.openai = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def ask_dalle(self):
        logger.debug(f"About to ask_dalle")
        response = self.openai.images.generate(
            model=self.model,
            prompt=self.prompt,
            size=self.size,
            quality=self.quality,
            n=self.n
        )
        image_url = response.data[0].url
        return image_url

    def generate_response(self):
        return self.ask_dalle()


class ReplicateMixin:
    def __init__(self):
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)


class ContentLLMMixin(AskGPTMixin, CalculateCostMixin, CreateTransactionMixin):
    """
    The product should not be changed, only yield the html result at the end of the process.
    """
    model = "gpt-4o-mini"

    def validate_generation(self):

        if self.multi_tenant_company.ai_points < 0:
            raise ValidationError(_("Insufficient AI points. Please purchase more."))

        return True

    def __init__(self, product, language_code, sales_channel_type=None):
        super().__init__()
        self.product = product
        self.multi_tenant_company = product.multi_tenant_company
        self.language_code = language_code
        self.sales_channel_type = sales_channel_type
        self.brand_prompt = None

    def _set_translation(self):
        self.translation = ProductTranslation.objects.filter(
            product=self.product,
            language=self.language_code
        ).first()

        # we can generate content for not existent translations
        # ex we have the english product then we switch to Dutch and we want to generate the translation
        if self.translation is None:
            self.translation = ProductTranslation.objects.filter(product=self.product).first()

    def _set_product_name(self):
        self.product_name = self.translation.name

    def _set_short_description(self):
        self.short_description = self.translation.short_description

    def _set_description(self):
        self.description = self.translation.description

    def _set_images(self):

        if settings.DEBUG:
            self.images = []
            return

        self.images = [i.media.image_web_url for i in MediaProductThrough.objects.filter(
            media__type=Media.IMAGE,
            product=self.product)]

    def _set_documents(self):

        if settings.DEBUG:
            self.documents = []
            return

        self.documents = [i.media.file_url() for i in MediaProductThrough.objects.filter(
            media__type=Media.FILE,
            product=self.product)]

    def _set_is_configurable(self):
        self.is_configurable = self.product.is_configurable()

    def _set_product_rule(self):
        self.product_rule = self.product.get_product_rule()

    def _set_property_values(self):
        from collections import defaultdict

        if self.is_configurable:
            property_values = defaultdict(list)

            for var in self.product.get_configurable_variations():
                prop_d = get_product_properties_dict(var)

                for k, v in prop_d.items():
                    property_values[k].extend(v)

            # Ensure you only return unique values. No duplicates.
            for k, v in property_values.items():
                property_values[k] = list(set(v))

            self.property_values = dict(property_values)
        else:
            self.property_values = get_product_properties_dict(self.product)

    def _set_brand_prompt(self):
        from properties.models import ProductProperty
        from llm.models import BrandCustomPrompt

        brand_prop = ProductProperty.objects.filter(
            product=self.product,
            property__internal_name='brand'
        ).select_related('value_select').first()

        self.brand_prompt = None
        if brand_prop and brand_prop.value_select:
            brand_value = brand_prop.value_select
            custom = BrandCustomPrompt.objects.filter(
                brand_value=brand_value,
                language=self.language_code,
                multi_tenant_company=self.multi_tenant_company,
            ).first()
            if not custom:
                custom = BrandCustomPrompt.objects.filter(
                    brand_value=brand_value,
                    language__isnull=True,
                    multi_tenant_company=self.multi_tenant_company,
                ).first()
            if custom:
                self.brand_prompt = custom.prompt

    @property
    def system_prompt(self):
        raise Exception("System prompt not configured.")

    @property
    def prompt(self):
        raise Exception("Prompt not configured.")

    def parse_response(self):
        """
        You can apply result parsing here.
        eg convert markdown to html, etc.
        by parsing self.response
        """
        pass

    def generate_response(self):
        self.validate_generation()
        self._set_translation()
        self._set_product_name()
        self._set_short_description()
        self._set_description()
        self._set_is_configurable()
        self._set_product_rule()
        self._set_property_values()
        self._set_brand_prompt()
        self._set_images()
        self._set_documents()

        self.response = self.ask_gpt()
        self.calculate_cost(self.response)
        self.text_response = self.get_text_response(self.response)
        self.parse_response()
        self._create_transaction()
        self._create_ai_generate_process()

        return self.text_response
