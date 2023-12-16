from django.urls import path
from .views import HsCodeListView, HsCodeDetailViev, HsCodeUpdateView, HsCodeDeleteView


app_name = 'customs'

urlpatterns = [
    path('hs-codes/', HsCodeListView.as_view(), name='hs_codes_list'),
    path('hs-codes/<str:pk>/', HsCodeDetailViev.as_view(), name='hs_code_detail'),
    path('hs-codes/<str:pk>/update/', HsCodeUpdateView.as_view(), name='hs_code_update'),
    path('hs-codes/<str:pk>/delete/', HsCodeDeleteView.as_view(), name='hs_code_delete'),
]
