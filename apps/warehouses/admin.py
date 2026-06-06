from django.contrib import admin

from apps.warehouses.models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("warehouse_code", "name", "city", "state", "capacity", "is_active", "is_deleted")
    list_filter = ("city", "state", "is_active", "is_deleted")
    search_fields = ("warehouse_code", "name", "city", "state")

