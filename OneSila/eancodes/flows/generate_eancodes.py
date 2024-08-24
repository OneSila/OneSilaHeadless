from eancodes.factories.generate_eancodes import GenerateEancodesFactory
from eancodes.models import EanCode


class GenerateEancodesFlow:
    def __init__(self, multi_tenant_company, prefix):
        self.factory = GenerateEancodesFactory(multi_tenant_company=multi_tenant_company, prefix=prefix)
        self.ean_codes = None

    def set_ean_codes(self):
        ids = []
        for ean in self.factory.ean_code_instances:
            ids.append(ean.id)

        self.ean_codes = EanCode.objects.filter(id__in=ids)

    def flow(self):
        self.factory.run()
        self.set_ean_codes()
