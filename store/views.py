from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView, CreateAPIView
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet

from core.models import Category, Product, Cart, CartItem, ShippingAddress, Order, OrderItem
from .filters import ProductFilter
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer, \
    ShippingAddressSerializer, OrderItemSerializer, OrderSerializer, PaymentSerializer


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 10


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)
    pagination_class = CustomPagination
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend]

    @swagger_auto_schema(
        operation_summary="Upload Product with Image",
        operation_description="Upload product details and an image.",
        manual_parameters=[
            openapi.Parameter(
                'image', openapi.IN_FORM, type=openapi.TYPE_FILE, description="Upload a product image"
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="List Products with Filters",
        operation_description="Retrieve a paginated list of products with optional filters.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              description="Filter by product name (contains search)"),
            openapi.Parameter('category', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description="Filter by category (choose from existing categories)"),
            openapi.Parameter('price_min', openapi.IN_QUERY, type=openapi.TYPE_NUMBER,
                              description="Filter by minimum price (greater than or equal)"),
            openapi.Parameter('price_max', openapi.IN_QUERY, type=openapi.TYPE_NUMBER,
                              description="Filter by maximum price (less than or equal)"),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class UserCartView(RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        if product.quantity < quantity:
            raise serializers.ValidationError(
                f"Not enough stock for {product.name}. Available: {product.quantity}, Requested: {quantity}")

        serializer.save(cart=cart)


class ShippingAddressViewSet(ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return ShippingAddress.objects.none()
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        cart = Cart.objects.get(user=self.request.user)

        if not cart.cart_items.exists():
            raise serializers.ValidationError("Your cart is empty.")

        total_price = sum(item.product.price * item.quantity for item in cart.cart_items.all())

        order = serializer.save(
            user=self.request.user,
            total_price=total_price,
            status='Pending',
            cart=cart
        )

        order_items = []
        for item in cart.cart_items.all():
            if item.product.quantity < item.quantity:
                raise serializers.ValidationError(
                    f"Not enough stock for {item.product.name}. Available: {item.product.quantity}")

            order_item = OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price * item.quantity
            )
            order_items.append(order_item)

            item.product.quantity -= item.quantity
            item.product.save()

        OrderItem.objects.bulk_create(order_items)
        cart.cart_items.all().delete()


class OrderItemViewSet(ReadOnlyModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return OrderItem.objects.none()
        return OrderItem.objects.filter(order__user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Retrieve Order Items",
        operation_description="Retrieve all items from the authenticated user's orders.",
        responses={
            200: OrderItemSerializer(many=True),
            401: "Unauthorized",
            404: "Order items not found"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CreatePaymentView(CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            201: openapi.Response("Payment processed successfully", PaymentSerializer),
            400: "No pending orders found for the user."
        }
    )
    def perform_create(self, serializer):
        user = self.request.user
        latest_order = Order.objects.filter(user=user, status='Pending').order_by('-created_at').first()

        if not latest_order:
            raise serializers.ValidationError("No pending orders found for the user.")

        payment = serializer.save(order=latest_order)

        payment.payment_status = 'Completed'
        payment.save()

        latest_order.status = 'Shipped'
        latest_order.save()

        return payment
