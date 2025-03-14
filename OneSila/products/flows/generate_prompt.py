from products.factories.generate_prompt import CreateProductPromptFactory
from billing.models import AiPointContentGenerateProcess


class AIGenerateContentFlow:
    def __init__(self, product, language):
        self.product = product
        self.language = language
        self.factory = CreateProductPromptFactory(product=product, language=language)
        self.generated_content = ''
        self.prompt = None
        self.images = None
        self.used_points = 0

    def get_generate_data(self):
        self.factory.run()
        self.prompt = self.factory.prompt
        self.images = self.factory.images

    def generate_content(self):
        content = AiPointContentGenerateProcess.objects.create_from_prompt(
            prompt=self.prompt,
            product=self.product,
            images=self.images,
            language=self.language,
        )
        self.generated_content = content.result
        self.used_points = content.transaction.points

    def flow(self):
        self.get_generate_data()
        self.generate_content()

        return self.generated_content