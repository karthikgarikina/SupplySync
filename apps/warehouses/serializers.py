from rest_framework import serializers


class WarehouseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    warehouse_code = serializers.CharField(required=False, allow_blank=False, max_length=20)
    name = serializers.CharField(required=True, allow_blank=False, max_length=150)
    location = serializers.CharField(required=True, allow_blank=False)
    city = serializers.CharField(required=True, allow_blank=False, max_length=100)
    state = serializers.CharField(required=True, allow_blank=False, max_length=100)
    pincode = serializers.CharField(required=True, allow_blank=False, max_length=10)
    capacity = serializers.IntegerField(required=True, min_value=1)
    is_active = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class WarehouseDetailSerializer(WarehouseSerializer):
    total_distinct_products = serializers.IntegerField(read_only=True)
    total_quantity_available = serializers.IntegerField(read_only=True)

