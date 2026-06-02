from decimal import Decimal

from rest_framework import serializers


class SalesOrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    unit_price = serializers.DecimalField(required=True, max_digits=12, decimal_places=2, min_value=Decimal("0.00"))


class SalesOrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    unit_price = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    total_price = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)


class SalesOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    order_number = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    customer_email = serializers.EmailField(required=True, allow_blank=False)
    customer_phone = serializers.CharField(required=True, allow_blank=False, max_length=20)
    shipping_address = serializers.CharField(required=True, allow_blank=False)
    warehouse_id = serializers.IntegerField(required=True)
    status = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)
    dispatched_at = serializers.DateTimeField(read_only=True, allow_null=True)
    delivered_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(read_only=True)
    notes = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    items = SalesOrderItemInputSerializer(required=True, many=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SalesOrderOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    order_number = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    customer_email = serializers.EmailField(read_only=True)
    customer_phone = serializers.CharField(read_only=True)
    shipping_address = serializers.CharField(read_only=True)
    warehouse_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)
    dispatched_at = serializers.DateTimeField(read_only=True, allow_null=True)
    delivered_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(read_only=True)
    notes = serializers.CharField(read_only=True, allow_null=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
