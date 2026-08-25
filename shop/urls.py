from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views
from . import api

app_name = 'shop'

# Register DRF viewsets with the router
router = DefaultRouter()
router.register(r'products', api.ProductViewSet, basename='api-product')
router.register(r'categories', api.CategoryViewSet, basename='api-category')

urlpatterns = [
    # --- DRF API Gateway ---
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='shop:schema'), name='swagger-ui'),

    # --- Home Page & Catalog Routes ---
    path('', views.home_page, name='home'),
    path('catalog/', views.product_list, name='product_list'),
    path('catalog/<slug:category_slug>/', views.product_list, name='product_list_by_category'),

    # --- Product Detail & Specs ---
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:product_slug>/specs/', views.product_specs, name='product_specs'),

    # --- Cart & Checkout ---
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.checkout_order, name='checkout_order'),

    # --- Customer Authentication & Settings ---
    path('accounts/register/', views.register_customer, name='register'),
    path('accounts/verify-otp/', views.verify_otp, name='verify_otp'),  # 👈 Added OTP verification route
    path('accounts/login/', views.login_customer, name='login'),
    path('accounts/logout/', views.logout_customer, name='logout'),
    path('profile/settings/', views.account_settings, name='account_settings'),
    path('profile/payment-methods/', views.payment_method_settings, name='payment_settings'),
    path('profile/settings/password/', views.change_password, name='change_password'),
    path('profile/orders/', views.order_history, name='order_history'),

    # --- Management & Auxiliary Pages ---
    path('management/product/add/', views.create_product, name='create_product'),
    path('management/product/add/<int:product_id>/', views.create_product, name='update_product'),
    path('management/audit-logs/', views.admin_purchase_history, name='admin_purchase_history'),
    path('pages/about-us/', views.about_us, name='about_us'),
    path('pages/contact-us/', views.contact_us, name='contact_us'),
]