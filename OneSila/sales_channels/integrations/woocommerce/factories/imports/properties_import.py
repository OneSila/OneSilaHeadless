# from .temp_structure import ImportProcessorTempStructureMixin
# from sales_channels.factories.imports import SalesChannelImportMixin
# from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin


# class WoocommerceProductImportProcessor(ImportProcessorTempStructureMixin, SalesChannelImportMixin, GetWoocommerceAPIMixin):
#     def __init__(self, import_process, sales_channel, language=None):
#         super().__init__(import_process, sales_channel, language)
#         self.api = self.get_api()

#     def get_total_instances(self) -> int:
#         # The self.temp_property_data is a dict of TempPropertyClass objects.
#         # Supplied by the ImportProcessorTempStructureMixin.
#         return len(self.temp_property_data.keys())

#     def get_properties_data(self):
#         # The self.temp_property_data is a dict of TempPropertyClass objects.
#         # Supplied by the ImportProcessorTempStructureMixin.
#         return self.temp_property_data.values()
