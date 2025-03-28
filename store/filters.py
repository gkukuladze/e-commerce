import django_filters

from core.models import Product, Category


class ProductFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(
        field_name="category",
        choices=lambda: [(category.id, category.name) for category in Category.objects.all()]
    )
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['name', 'category', 'price_min', 'price_max']
