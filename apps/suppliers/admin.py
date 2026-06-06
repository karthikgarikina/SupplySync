from django.contrib import admin

from apps.suppliers.models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("supplier_code", "name", "contact_person", "email", "city", "state", "is_active", "is_deleted")
    list_filter = ("city", "state", "is_active", "is_deleted")
    search_fields = ("supplier_code", "name", "contact_person", "email")

