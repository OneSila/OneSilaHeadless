import openai
from django.conf import settings

from media.models import MediaProductThrough
from products.models import ProductTranslation
from properties.helpers import get_product_properties_dict

import logging
logger = logging.getLogger(__name__)


class OpenAIMixin:
    def __init__(self):
        self.openai = openai.Client(api_key=settings.OPENAI_API_KEY)


class AskGPTMixin(OpenAIMixin):
    model = 'gpt-4o-mini'
    temperature = 0.7
    max_tokens = 2000

    def ask_gpt(self):
        logger.debug(f"About to ask_gpt")
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content.strip()


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


class ContentLLMMixin(AskGPTMixin):
    """
    The product should not be changed, only yield the html result at the end of the process.
    """
    model = "gpt-4o-mini"

    def __init__(self, product, language_code):
        super().__init__()
        self.product = product
        self.language_code = language_code

    def _set_translation(self):
        self.translation = ProductTranslation.objects.filter(
            product=self.product,
            language=self.language_code
        ).first()

    def _set_product_name(self):
        self.product_name = self.translation.name

    def _set_short_description(self):
        self.short_description = self.translation.short_description

    def _set_description(self):
        self.description = self.translation.description

    def _set_images(self):
        self.images = [i.media.image_web_url for i in MediaProductThrough.objects.filter(product=self.product)]

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

    @property
    def system_prompt(self):
        raise Exception("System prompt not configured.")

    @property
    def prompt(self):
        raise Exception("Prompt not configured.")

    def generate_response(self):
        self._set_translation()
        self._set_product_name()
        self._set_short_description()
        self._set_description()
        self._set_is_configurable()
        self._set_product_rule()
        self._set_property_values()
        self._set_images()
        self.response = self.ask_gpt()
        return self.response
