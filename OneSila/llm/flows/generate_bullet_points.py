from llm.factories.content import BulletPointsLLM


class AIGenerateBulletPointsFlow:
    def __init__(self, product, language, return_one=False):
        self.product = product
        self.language = language
        self.return_one = return_one
        self.existing_bullet_points = self._get_existing_bullet_points()
        self.factory = BulletPointsLLM(
            product=product,
            language_code=language,
            return_one=return_one,
            existing_bullet_points=self.existing_bullet_points,
        )
        self.generated_points = []
        self.used_points = 0

    def _get_existing_bullet_points(self):
        translations = self.product.translations.prefetch_related("bullet_points")
        translation = translations.filter(language=self.language).first() or translations.first()

        if not translation:
            return []

        return [
            bp
            for bp in translation.bullet_points.order_by("sort_order").values_list("text", flat=True)
            if bp
        ]

    def generate_points(self):
        self.factory.generate_response()
        process = self.factory.ai_process
        self.generated_points = self.factory.bullet_points
        if self.return_one and self.generated_points:
            self.generated_points = self.generated_points[:1]
        self.used_points = process.transaction.points

    def flow(self):
        self.generate_points()
        return self.generated_points

