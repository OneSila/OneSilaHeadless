from properties.models import PropertySelectValue


class MergePropertySelectValueFactory:
    def __init__(self, *, multi_tenant_company_id, source_ids, target_id):
        self.multi_tenant_company_id = multi_tenant_company_id
        self.source_ids = source_ids
        self.target_id = target_id

    def run(self):
        source_qs = PropertySelectValue.objects.filter(
            id__in=self.source_ids,
            multi_tenant_company_id=self.multi_tenant_company_id,
        )
        target_instance = PropertySelectValue.objects.get(
            id=self.target_id,
            multi_tenant_company_id=self.multi_tenant_company_id,
        )
        return source_qs.merge(target_instance)
