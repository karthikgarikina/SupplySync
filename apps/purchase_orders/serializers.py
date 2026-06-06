from decimal import Decimal

from rest_framework import serializers


class PurchaseOrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity_ordered = serializers.IntegerField(required=True, min_value=1)
    unit_price = serializers.DecimalField(required=True, max_digits=12, decimal_places=2, min_value=Decimal("0.00"))


class PurchaseOrderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    quantity_ordered = serializers.IntegerField(read_only=True)
    quantity_received = serializers.IntegerField(read_only=True)
    unit_price = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    total_price = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)


class PurchaseOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    po_number = serializers.CharField(read_only=True)
    supplier_id = serializers.IntegerField(required=True)
    warehouse_id = serializers.IntegerField(required=True)
    status = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    actual_delivery_date = serializers.DateField(read_only=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    items = PurchaseOrderItemInputSerializer(required=False, many=True)
    created_by_id = serializers.IntegerField(read_only=True)
    approved_by_id = serializers.IntegerField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class PurchaseOrderOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    po_number = serializers.CharField(read_only=True)
    supplier_id = serializers.IntegerField(read_only=True)
    warehouse_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)
    expected_delivery_date = serializers.DateField(read_only=True, allow_null=True)
    actual_delivery_date = serializers.DateField(read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(read_only=True)
    approved_by_id = serializers.IntegerField(read_only=True, allow_null=True)
    notes = serializers.CharField(read_only=True, allow_null=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class PurchaseOrderReceiveItemSerializer(serializers.Serializer):
    po_item_id = serializers.IntegerField(required=True)
    quantity_received = serializers.IntegerField(required=True, min_value=1)


class PurchaseOrderReceiveSerializer(serializers.Serializer):
    items = PurchaseOrderReceiveItemSerializer(required=True, many=True)
    actual_delivery_date = serializers.DateField(required=False, allow_null=True)


class PurchaseOrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
