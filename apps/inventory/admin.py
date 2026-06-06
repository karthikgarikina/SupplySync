from django.contrib import admin

from apps.inventory.models import Inventory, InventoryTransaction


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity_available", "quantity_reserved", "quantity_damaged", "is_deleted")
    list_filter = ("warehouse", "is_deleted")
    search_fields = ("product__sku", "product__name", "warehouse__warehouse_code", "warehouse__name")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "transaction_type", "quantity", "reference_id", "performed_by", "created_at")
    list_filter = ("transaction_type", "warehouse", "created_at")
    search_fields = ("product__sku", "warehouse__warehouse_code", "reference_id", "performed_by__email")
    readonly_fields = ("product", "warehouse", "transaction_type", "quantity", "reference_id", "performed_by", "notes", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

