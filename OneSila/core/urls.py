from django.urls import path
from core.views import EmptyTemplateView


app_name = 'core'

urlpatterns = [
    path('dashboard/', EmptyTemplateView.as_view(), name='dashboard'),
    path('auth/login/', EmptyTemplateView.as_view(), name='auth_login'),
    path('auth/login/token/<str:token>/', EmptyTemplateView.as_view(), name='auth_token_login'),
    path('auth/login/token/request/', EmptyTemplateView.as_view(), name='auth_token_login_request'),
    path('auth/register/', EmptyTemplateView.as_view(), name='auth_register'),
    path('auth/register/accept-invite/<str:token>/', EmptyTemplateView.as_view(), name='auth_register_accept_invite'),
    path('auth/register/company/', EmptyTemplateView.as_view(), name='auth_register_company'),
    path('auth/recover/<str:token>/', EmptyTemplateView.as_view(), name='auth_recover'),
    path('auth/password/change/', EmptyTemplateView.as_view(), name='auth_change_password'),
    path('profile/', EmptyTemplateView.as_view(), name='profile'),
    path('company/profile/', EmptyTemplateView.as_view(), name='company_profile'),
]
