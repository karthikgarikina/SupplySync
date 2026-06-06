from django.contrib import admin

from apps.sales_orders.models import SalesOrder, SalesOrderItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "warehouse", "status", "total_amount", "created_by")
    list_filter = ("status", "warehouse", "is_deleted")
    search_fields = ("order_number", "customer_name", "customer_email", "warehouse__warehouse_code")
    inlines = [SalesOrderItemInline]


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ("sales_order", "product", "quantity", "unit_price", "total_price")
    search_fields = ("sales_order__order_number", "product__sku", "product__name")

