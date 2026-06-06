from django.contrib import admin

from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "unit_price", "reorder_level", "is_active", "is_deleted")
    list_filter = ("category", "is_active", "is_deleted")
    search_fields = ("sku", "name", "description")

