from llm.factories.content import BulletPointsLLM
from sales_channels.helpers import build_content_payload

GENERATE_BULLET_POINTS_CONTENT_FLAGS = {"bulletPoints": True}


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
        content_payload = build_content_payload(
            product=self.product,
            sales_channel=None,
            language=self.language,
            flags_override=GENERATE_BULLET_POINTS_CONTENT_FLAGS,
        )
        return [point for point in content_payload.get("bulletPoints", []) if point]

    def generate_points(self):
        self.factory.generate_response()
        process = self.factory.ai_process
        self.generated_points = self.factory.bullet_points
        self.used_points = process.transaction.points

    def flow(self):
        self.generate_points()
        return self.generated_points
