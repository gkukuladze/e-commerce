from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, UserCartView, ProductViewSet, \
    OrderItemViewSet, OrderViewSet, CreatePaymentView, CartItemViewSet

app_name = 'store'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart-items', CartItemViewSet, basename='cart-item')
router.register(r'order_items', OrderItemViewSet, basename='order-item')
router.register(r'order', OrderViewSet, basename='order')

urlpatterns = [
    path('cart/', UserCartView.as_view(), name='user-cart'),
    path('payment/', CreatePaymentView.as_view(), name='payment'),
    path('', include(router.urls)),
]
