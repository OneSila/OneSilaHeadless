# from sales_prices.models import SalesPriceListAssign, SalesPriceListItem, SalesPrice


# class OrderItemPriceSetFactory:
#     '''
#     This factory is placed in prices as all pricing will originate from this app.
#     This class is responsible for pupulating pricing in the orderitems.
#     '''

#     def __init__(self, order_item, save=False):
#         self.order_item = order_item
#         self.product = order_item.product
#         self.order = self.order_item.order
#         self.contact = self.order.contact
#         self.currency = self.order.currency
#         self.save = save

#     def _detect_pricelist_item(self):
#         '''
#         Lets see if there is a pricelist attached to the contact, and if that product is present in there.
#         '''
#         if not self.order_item.price:
#             try:
#                 assign = SalesPriceListAssign.objects.get(contact=self.contact)
#                 try:
#                     pricelist = assign.salespricelist
#                     item = pricelist.salespricelistitem_set.get(product=self.product)

#                     self.order_item.price = item.salesprice
#                 except SalesPriceListItem.DoesNotExist:
#                     pass
#             except SalesPriceListAssign.DoesNotExist:
#                 pass

#     def _detect_salesprice(self):
#         '''
#         Lets see what the default price for this product is.
#         '''
#         if not self.order_item.price:
#             try:
#                 salesprice = SalesPrice.objects.get(product=self.product, currency=self.currency)
#                 self.order_item.price = salesprice.amount
#             except SalesPrice.DoesNotExist:
#                 pass

#     def _save_pricing(self):
#         '''
#         Save the price on the object,and save is required.
#         '''
#         if self.save:
#             self.order_item.save()

#     def run(self):
#         self._detect_pricelist_item()
#         self._detect_salesprice()
#         self._save_pricing()
