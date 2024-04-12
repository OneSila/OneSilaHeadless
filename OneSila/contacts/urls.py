from .views import AddressListView, AddressDetailView, AddressUpdateView, \
    AddressDeleteView, CompanyListView, CompanyDetailViev, CompanyUpdateView, \
    CompanyDeleteView, CustomerListView, CustomerDetailViev, CustomerUpdateView, \
    CustomerDeleteView, InfluencerListView, InfluencerDetailViev, InfluencerUpdateView, \
    InfluencerDeleteView, InternalCompanyListView, InternalCompanyDetailViev, \
    InternalCompanyUpdateView, InternalCompanyDeleteView, InvoiceAddressListView, \
    InvoiceAddressDetailView, InvoiceAddressUpdateView, InvoiceAddressDeleteView, \
    PersonListView, PersonDetailViev, PersonUpdateView, PersonDeleteView, ShippingAddressListView, \
    ShippingAddressDetailView, ShippingAddressUpdateView, ShippingAddressDeleteView, SupplierListView, \
    SupplierDetailViev, SupplierUpdateView, SupplierDeleteView
from django.urls import path

app_name = "contacts"

urlpatterns = [
    path('addresss/', AddressListView.as_view(), name='addresss_list'),
    path('addresss/<str:pk>/', AddressDetailView.as_view(), name='address_detail'),
    path('addresss/<str:pk>/update/', AddressUpdateView.as_view(), name='address_update'),
    path('addresss/<str:pk>/delete/', AddressDeleteView.as_view(), name='address_delete'),
    path('companies/', CompanyListView.as_view(), name='companies_list'),
    path('companies/<str:pk>/', CompanyDetailViev.as_view(), name='company_detail'),
    path('companies/<str:pk>/update/', CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<str:pk>/delete/', CompanyDeleteView.as_view(), name='company_delete'),
    path('customers/', CustomerListView.as_view(), name='customers_list'),
    path('customers/<str:pk>/', CustomerDetailViev.as_view(), name='customer_detail'),
    path('customers/<str:pk>/update/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<str:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
    path('influencers/', InfluencerListView.as_view(), name='influencers_list'),
    path('influencers/<str:pk>/', InfluencerDetailViev.as_view(), name='influencer_detail'),
    path('influencers/<str:pk>/update/', InfluencerUpdateView.as_view(), name='influencer_update'),
    path('influencers/<str:pk>/delete/', InfluencerDeleteView.as_view(), name='influencer_delete'),
    path('interal-companies/', InternalCompanyListView.as_view(), name='interal_companies_list'),
    path('interal-companies/<str:pk>/', InternalCompanyDetailViev.as_view(), name='internal_company_detail'),
    path('interal-companies/<str:pk>/update/', InternalCompanyUpdateView.as_view(), name='internal_company_update'),
    path('interal-companies/<str:pk>/delete/', InternalCompanyDeleteView.as_view(), name='internal_company_delete'),
    path('invoice-addresss/', InvoiceAddressListView.as_view(), name='invoice_addresss_list'),
    path('invoice-addresss/<str:pk>/', InvoiceAddressDetailView.as_view(), name='invoice_address_detail'),
    path('invoice-addresss/<str:pk>/update/', InvoiceAddressUpdateView.as_view(), name='invoice_address_update'),
    path('invoice-addresss/<str:pk>/delete/', InvoiceAddressDeleteView.as_view(), name='invoice_address_delete'),
    path('people/', PersonListView.as_view(), name='people_list'),
    path('people/<str:pk>/', PersonDetailViev.as_view(), name='person_detail'),
    path('people/<str:pk>/update/', PersonUpdateView.as_view(), name='person_update'),
    path('people/<str:pk>/delete/', PersonDeleteView.as_view(), name='person_delete'),
    path('shipping-addresss/', ShippingAddressListView.as_view(), name='shipping_addresss_list'),
    path('shipping-addresss/<str:pk>/', ShippingAddressDetailView.as_view(), name='shipping_address_detail'),
    path('shipping-addresss/<str:pk>/update/', ShippingAddressUpdateView.as_view(), name='shipping_address_update'),
    path('shipping-addresss/<str:pk>/delete/', ShippingAddressDeleteView.as_view(), name='shipping_address_delete'),
    path('suppliers/', SupplierListView.as_view(), name='suppliers_list'),
    path('suppliers/<str:pk>/', SupplierDetailViev.as_view(), name='supplier_detail'),
    path('suppliers/<str:pk>/update/', SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<str:pk>/delete/', SupplierDeleteView.as_view(), name='supplier_delete')
]
