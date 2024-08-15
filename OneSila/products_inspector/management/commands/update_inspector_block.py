from django.core.management.base import BaseCommand
from products_inspector.models import Inspector
from products_inspector.factories.inspector_block import InspectorBlockCreateOrUpdateFactory

class Command(BaseCommand):
    help = 'Update a specific block in all inspectors based on the provided error_code'

    def add_arguments(self, parser):
        parser.add_argument('error_code', type=int, help='The error code of the block to update')

    def handle(self, *args, **kwargs):
        error_code = kwargs['error_code']
        inspectors = Inspector.objects.all()
        total_inspectors = inspectors.count()

        self.stdout.write(self.style.NOTICE(f'Updating block with error_code {error_code} for {total_inspectors} inspectors...'))

        for index, inspector in enumerate(inspectors, start=1):
            factory = InspectorBlockCreateOrUpdateFactory(inspector, error_code)
            factory.run()
            self.stdout.write(self.style.SUCCESS(f'[{index}/{total_inspectors}] Updated block {error_code} for inspector of product {inspector.product.sku}'))

        self.stdout.write(self.style.SUCCESS('All blocks updated successfully.'))
