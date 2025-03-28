from rest_framework import serializers

from core.models import Category, Product, Cart, CartItem, ShippingAddress, Order, OrderItem, Payment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'description', 'price', 'quantity', 'image']

    def create(self, validated_data):
        return Product.objects.create(**validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_details = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'product_details']

    @staticmethod
    def get_product_details(obj):
        product_data = ProductSerializer(obj.product).data
        product_data.pop('quantity', None)
        return product_data


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'cart_items', 'total_price']


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['phone_number', 'address', 'city', 'country', 'postal_code']


class ProductForOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']


class ProductForOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'description', 'price', 'image']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductForOrderItemSerializer(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, source='price', read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    shipping_address = serializers.PrimaryKeyRelatedField(queryset=ShippingAddress.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    payment_status = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'shipping_address', 'items', 'total_price', 'payment_status', 'created_at']
        read_only_fields = ['status', 'total_price', 'items', 'user', 'payment_status', 'created_at']

    def get_items(self, obj):
        order_items = obj.items.all()
        return [
            ProductForOrderSerializer(order_item.product).data
            for order_item in order_items
        ]

    def get_payment_status(self, obj):
        return obj.payment_status


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount', 'payment_date']
        read_only_fields = ['amount', 'payment_date']

    def create(self, validated_data):
        order = validated_data['order']
        validated_data['amount'] = order.total_price

        validated_data['payment_status'] = 'Pending'

        return super().create(validated_data)
