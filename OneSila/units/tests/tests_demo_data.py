from core.tests.tests_schemas.tests_queries import TransactionTestCase
from django.contrib.contenttypes.models import ContentType
from model_bakery import baker


class DemoDataGeneratorTestCase(TransactionTestCase):
    def test_class_based_generator_creates_relation(self):
        from units.demo_data import UnitGenerator
        from core.models import MultiTenantCompany

        mtc = baker.make(MultiTenantCompany)

        g = UnitGenerator(mtc)
        g.generate()

        instance = g.generated_instances[0]
        content_type = ContentType.objects.get_for_model(instance)
        object_id = instance.id

        result = mtc.demodatarelation_set.filter(content_type=content_type, object_id=object_id)

        self.assertTrue(result.exists())
