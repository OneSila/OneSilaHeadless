from llm.factories.content import BulletPointsLLM


class AIGenerateBulletPointsFlow:
    def __init__(self, product, language):
        self.product = product
        self.language = language
        self.factory = BulletPointsLLM(product=product, language_code=language)
        self.generated_points = []
        self.used_points = 0

    def generate_points(self):
        self.factory.generate_response()
        process = self.factory.ai_process
        self.generated_points = self.factory.bullet_points
        self.used_points = process.transaction.points

    def flow(self):
        self.generate_points()
        return self.generated_points

