from llm.factories.content import DescriptionGenLLM, ShortDescriptionLLM
from llm.schema.types.input import ContentAiGenerateType


class AIGenerateContentFlow:
    def __init__(self, product, language, content_type):
        factory_map = {
            ContentAiGenerateType.DESCRIPTION: DescriptionGenLLM,
            ContentAiGenerateType.SHORT_DESCRIPTION: ShortDescriptionLLM,
        }
        factory_class = factory_map.get(content_type, DescriptionGenLLM)

        self.product = product
        self.language = language
        self.factory = factory_class(product=product, language_code=language)
        self.generated_content = ''
        self.used_points = 0

    def generate_content(self):
        self.factory.generate_response()
        process = self.factory.ai_process

        self.generated_content = process.result
        self.used_points = process.transaction.points

    def flow(self):
        self.generate_content()
        return self.generated_content