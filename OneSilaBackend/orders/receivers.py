# #
# # Signals
# #

# @receiver(pre_save, sender=Order)
# def instockorder_topick_signal(sender, instance, **kwargs):
#     '''
#     If the order in in stock, then mark ik as to pick
#     '''
#     if instance.on_stock and \
#             (instance.status in Order.UNPROCESSED or instance.status in Order.IN_PRODUCTION):
#         instance.status = Order.TO_PICK


# @receiver(post_save, sender='inventory.ProductStock')
# def inventory_change__topick_signal(sender, instance, **kwargs):
#     '''
#     If the inventory changes, and the product gets stock, then check if you have
#     orders that have become in stock
#     '''
#     product = instance.product
#     if product.stock.physical():
#         unprocessed_orders = [i.order for i in product.orderitem_set.filter(order__status=Order.PENDING)]

#         for order in unprocessed_orders:
#             if order.on_stock:
#                 order.status = Order.TO_PICK
#                 order.save()
