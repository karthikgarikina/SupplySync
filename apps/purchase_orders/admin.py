from django.contrib import admin

from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "warehouse", "status", "total_amount", "created_by", "approved_by")
    list_filter = ("status", "warehouse", "supplier", "is_deleted")
    search_fields = ("po_number", "supplier__name", "warehouse__warehouse_code")
    inlines = [PurchaseOrderItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "product", "quantity_ordered", "quantity_received", "unit_price", "total_price")
    search_fields = ("purchase_order__po_number", "product__sku", "product__name")

