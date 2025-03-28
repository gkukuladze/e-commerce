from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(
        blank=True, default="No description available.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image = models.ImageField(
        upload_to='product_images/', blank=True, null=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        ordering = ['-create_date']
        verbose_name_plural = "Products"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user.email}"

    @property
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.cart_items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField()
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"Shipping Address for {self.user.email}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(
        ShippingAddress, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.email} - {self.status}"

    @property
    def payment_status(self):
        return self.payment.payment_status if hasattr(self, "payment") else "Pending"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ])
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.payment_status}"
