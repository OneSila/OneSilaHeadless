from django.core.management.base import BaseCommand
from products.models import Product
from products_inspector.factories.inspector import InspectorCreateOrUpdateFactory

class Command(BaseCommand):
    help = 'Update all inspectors with clear_blocks=True and run_sync=False'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        total_products = products.count()

        self.stdout.write(self.style.NOTICE(f'Updating inspectors for {total_products} products...'))

        for index, product in enumerate(products, start=1):
            factory = InspectorCreateOrUpdateFactory(product, clear_blocks=True, run_sync=False)
            factory.run()
            self.stdout.write(self.style.SUCCESS(f'[{index}/{total_products}] Updated inspector for product {product.sku}'))

        self.stdout.write(self.style.SUCCESS('All inspectors updated successfully.'))
