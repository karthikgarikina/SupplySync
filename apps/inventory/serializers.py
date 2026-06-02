from rest_framework import serializers

from apps.inventory.models import TransactionType


class InventoryAdjustSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    warehouse_id = serializers.IntegerField(required=True)
    transaction_type = serializers.ChoiceField(required=True, choices=TransactionType.choices)
    quantity = serializers.IntegerField(required=True, min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class InventoryTransferSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    source_warehouse_id = serializers.IntegerField(required=True)
    destination_warehouse_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class InventoryTransactionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    warehouse_id = serializers.IntegerField(read_only=True)
    transaction_type = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    reference_id = serializers.CharField(read_only=True, allow_null=True)
    performed_by_id = serializers.IntegerField(read_only=True)
    notes = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class LowStockAlertSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    warehouse_id = serializers.IntegerField(read_only=True)
    warehouse_name = serializers.CharField(read_only=True)
    quantity_available = serializers.IntegerField(read_only=True)
    reorder_level = serializers.IntegerField(read_only=True)
    deficit = serializers.IntegerField(read_only=True)


class InventorySnapshotSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    warehouse_id = serializers.IntegerField(read_only=True)
    warehouse_name = serializers.CharField(read_only=True)
    quantity_available = serializers.IntegerField(read_only=True)
    quantity_reserved = serializers.IntegerField(read_only=True)
    quantity_damaged = serializers.IntegerField(read_only=True)
    last_updated_at = serializers.DateTimeField(read_only=True)

