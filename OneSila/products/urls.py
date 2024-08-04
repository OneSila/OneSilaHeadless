from django.urls import path
from .views import BundleProductListView, BundleProductDetailViev, BundleProductUpdateView, BundleProductDeleteView, BundleVariationListView, BundleVariationDetailViev, BundleVariationUpdateView, BundleVariationDeleteView, ProductListView, ProductDetailViev, ProductUpdateView, ProductDeleteView, ProductTranslationListView, ProductTranslationDetailViev, ProductTranslationUpdateView, ProductTranslationDeleteView, SimpleProductListView, SimpleProductDetailViev, SimpleProductUpdateView, SimpleProductDeleteView, UmbrellaProductListView, UmbrellaProductDetailViev, UmbrellaProductUpdateView, UmbrellaProductDeleteView, ConfigurableVariationListView, ConfigurableVariationDetailViev, ConfigurableVariationUpdateView, ConfigurableVariationDeleteView

app_name = 'products'

urlpatterns = [
    path('bundle-products/', BundleProductListView.as_view(), name='bundle_products_list'),
    path('bundle-products/<str:pk>/', BundleProductDetailViev.as_view(), name='bundle_product_detail'),
    path('bundle-products/<str:pk>/update/', BundleProductUpdateView.as_view(), name='bundle_product_update'),
    path('bundle-products/<str:pk>/delete/', BundleProductDeleteView.as_view(), name='bundle_product_delete'),
    path('bundle-variations/', BundleVariationListView.as_view(), name='bundle_variations_list'),
    path('bundle-variations/<str:pk>/', BundleVariationDetailViev.as_view(), name='bundle_variation_detail'),
    path('bundle-variations/<str:pk>/update/', BundleVariationUpdateView.as_view(), name='bundle_variation_update'),
    path('bundle-variations/<str:pk>/delete/', BundleVariationDeleteView.as_view(), name='bundle_variation_delete'),
    path('products/', ProductListView.as_view(), name='products_list'),
    path('products/<str:pk>/', ProductDetailViev.as_view(), name='product_detail'),
    path('products/<str:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<str:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('product-translations/', ProductTranslationListView.as_view(), name='product_translations_list'),
    path('product-translations/<str:pk>/', ProductTranslationDetailViev.as_view(), name='product_translation_detail'),
    path('product-translations/<str:pk>/update/', ProductTranslationUpdateView.as_view(), name='product_translation_update'),
    path('product-translations/<str:pk>/delete/', ProductTranslationDeleteView.as_view(), name='product_translation_delete'),
    path('product-variations/', SimpleProductListView.as_view(), name='simple_products_list'),
    path('product-variations/<str:pk>/', SimpleProductDetailViev.as_view(), name='simple_product_detail'),
    path('product-variations/<str:pk>/update/', SimpleProductUpdateView.as_view(), name='simple_product_update'),
    path('product-variations/<str:pk>/delete/', SimpleProductDeleteView.as_view(), name='simple_product_delete'),
    path('umbrella-products/', UmbrellaProductListView.as_view(), name='umbrella_products_list'),
    path('umbrella-products/<str:pk>/', UmbrellaProductDetailViev.as_view(), name='umbrella_product_detail'),
    path('umbrella-products/<str:pk>/update/', UmbrellaProductUpdateView.as_view(), name='umbrella_product_update'),
    path('umbrella-products/<str:pk>/delete/', UmbrellaProductDeleteView.as_view(), name='umbrella_product_delete'),
    path('configurable-variations/', ConfigurableVariationListView.as_view(), name='configurable_variations_list'),
    path('configurable-variations/<str:pk>/', ConfigurableVariationDetailViev.as_view(), name='configurable_variation_detail'),
    path('configurable-variations/<str:pk>/update/', ConfigurableVariationUpdateView.as_view(), name='configurable_variation_update'),
    path('configurable-variations/<str:pk>/delete/', ConfigurableVariationDeleteView.as_view(), name='configurable_variation_delete'),
]
