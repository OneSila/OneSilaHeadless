from core.documents.views import DocumentView
from core.views import EmptyTemplateView
from .models import Order, OrderItem, OrderNote


class OrderConfirmationFileView(DocumentView):
    model = Order


class OrderListView(EmptyTemplateView):
    pass


class OrderDetailViev(EmptyTemplateView):
    pass


class OrderUpdateView(EmptyTemplateView):
    pass


class OrderDeleteView(EmptyTemplateView):
    pass


class OrderItemListView(EmptyTemplateView):
    pass


class OrderItemDetailViev(EmptyTemplateView):
    pass


class OrderItemUpdateView(EmptyTemplateView):
    pass


class OrderItemDeleteView(EmptyTemplateView):
    pass


class OrderNoteListView(EmptyTemplateView):
    pass


class OrderNoteDetailViev(EmptyTemplateView):
    pass


class OrderNoteUpdateView(EmptyTemplateView):
    pass


class OrderNoteDeleteView(EmptyTemplateView):
    pass
