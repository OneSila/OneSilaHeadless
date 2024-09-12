# from inventory.models import Inventory
# from ..mixins import RemoteInstanceUpdateFactory, ProductAssignmentMixin
#
#
# class RemoteInventoryUpdateFactory(RemoteInstanceUpdateFactory, ProductAssignmentMixin):
#     local_model_class = Inventory
#
#     def __init__(self, local_instance, sales_channel):
#         super().__init__(local_instance, sales_channel)
#         self.remote_product = self.get_remote_product(local_instance.product)
#         self.remote_instance = None
#
#
#     def preflight_check(self):
#         """
#         Checks that the RemoteProduct and associated SalesChannelViewAssign exist before proceeding.
#         Also sets the remote_instance if conditions are met.
#         """
#         if not self.remote_product:
#             return False
#
#         if not self.assigned_to_website():
#             return False
#
#         # Set the remote_instance for the factory based on existing data
#         try:
#             self.remote_instance = self.remote_model_class.objects.get(
#                 remote_product=self.remote_product
#             )
#         except self.remote_model_class.DoesNotExist:
#             return False
#
#         # Check if the quantity matches the salable quantity
#         if self.remote_instance.quantity == self.local_instance.salable():
#             return False
#
#         return True
#
#     def get_remote_instance(self):
#         """
#         Override to prevent fetching in the default way since it is already set in preflight_check.
#         """
#         pass
