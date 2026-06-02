from decimal import Decimal

from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(required=False, allow_blank=False, max_length=50)
    name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    category_id = serializers.IntegerField(required=True)
    unit_price = serializers.DecimalField(required=True, max_digits=12, decimal_places=2, min_value=Decimal("0.00"))
    unit_of_measure = serializers.CharField(required=True, allow_blank=False, max_length=20)
    reorder_level = serializers.IntegerField(required=False, min_value=0)
    is_active = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProductDetailSerializer(ProductSerializer):
    inventory_by_warehouse = serializers.ListField(read_only=True)
