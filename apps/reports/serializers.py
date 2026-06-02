from rest_framework import serializers


class DashboardReportSerializer(serializers.Serializer):
    total_warehouses = serializers.IntegerField(read_only=True)
    total_products = serializers.IntegerField(read_only=True)
    total_suppliers = serializers.IntegerField(read_only=True)
    total_inventory_value = serializers.DecimalField(read_only=True, max_digits=16, decimal_places=2)
    open_purchase_orders = serializers.IntegerField(read_only=True)
    pending_sales_orders = serializers.IntegerField(read_only=True)
    low_stock_product_count = serializers.IntegerField(read_only=True)
    top_selling_products = serializers.ListField(read_only=True)
    recent_transactions = serializers.ListField(read_only=True)


class InventoryValuationReportSerializer(serializers.Serializer):
    grand_total_value = serializers.DecimalField(read_only=True, max_digits=16, decimal_places=2)
    warehouses = serializers.ListField(read_only=True)


class PurchaseOrderSummaryReportSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField(read_only=True)
    total_value = serializers.DecimalField(read_only=True, max_digits=16, decimal_places=2)
    breakdown_by_status = serializers.ListField(read_only=True)
    top_suppliers = serializers.ListField(read_only=True)


class SalesOrderSummaryReportSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(read_only=True, max_digits=16, decimal_places=2)
    average_order_value = serializers.DecimalField(read_only=True, max_digits=16, decimal_places=2)
    breakdown_by_status = serializers.ListField(read_only=True)
    top_products_by_revenue = serializers.ListField(read_only=True)

