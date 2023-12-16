from django.urls import path
from .views import ProductPropertyListView, ProductPropertyDetailViev, ProductPropertyUpdateView, ProductPropertyDeleteView, PropertyListView, PropertyDetailViev, PropertyUpdateView, PropertyDeleteView, PropertySelectValueListView, PropertySelectValueDetailViev, PropertySelectValueUpdateView, PropertySelectValueDeleteView, PropertySelectValueTranslationListView, PropertySelectValueTranslationDetailViev, PropertySelectValueTranslationUpdateView, PropertySelectValueTranslationDeleteView, PropertyTranslationListView, PropertyTranslationDetailViev, PropertyTranslationUpdateView, PropertyTranslationDeleteView

app_name = 'properties'

urlpatterns = [
    path('product-properties/', ProductPropertyListView.as_view(), name='product_properties_list'),
    path('product-properties/<str:pk>/', ProductPropertyDetailViev.as_view(), name='product_property_detail'),
    path('product-properties/<str:pk>/update/', ProductPropertyUpdateView.as_view(), name='product_property_update'),
    path('product-properties/<str:pk>/delete/', ProductPropertyDeleteView.as_view(), name='product_property_delete'),
    path('properties/', PropertyListView.as_view(), name='properties_list'),
    path('properties/<str:pk>/', PropertyDetailViev.as_view(), name='property_detail'),
    path('properties/<str:pk>/update/', PropertyUpdateView.as_view(), name='property_update'),
    path('properties/<str:pk>/delete/', PropertyDeleteView.as_view(), name='property_delete'),
    path('property-select-values/', PropertySelectValueListView.as_view(), name='property_select_values_list'),
    path('property-select-values/<str:pk>/', PropertySelectValueDetailViev.as_view(), name='property_select_value_detail'),
    path('property-select-values/<str:pk>/update/', PropertySelectValueUpdateView.as_view(), name='property_select_value_update'),
    path('property-select-values/<str:pk>/delete/', PropertySelectValueDeleteView.as_view(), name='property_select_value_delete'),
    path('property-select-value-translations/', PropertySelectValueTranslationListView.as_view(), name='property_select_value_translations_list'),
    path('property-select-value-translations/<str:pk>/', PropertySelectValueTranslationDetailViev.as_view(), name='property_select_value_translation_detail'),
    path('property-select-value-translations/<str:pk>/update/', PropertySelectValueTranslationUpdateView.as_view(), name='property_select_value_translation_update'),
    path('property-select-value-translations/<str:pk>/delete/', PropertySelectValueTranslationDeleteView.as_view(), name='property_select_value_translation_delete'),
    path('property-translations/', PropertyTranslationListView.as_view(), name='property_translations_list'),
    path('property-translations/<str:pk>/', PropertyTranslationDetailViev.as_view(), name='property_translation_detail'),
    path('property-translations/<str:pk>/update/', PropertyTranslationUpdateView.as_view(), name='property_translation_update'),
    path('property-translations/<str:pk>/delete/', PropertyTranslationDeleteView.as_view(), name='property_translation_delete'),
]
