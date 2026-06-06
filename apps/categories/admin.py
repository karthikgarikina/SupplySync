from django.contrib import admin

from apps.categories.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_code", "name", "parent_category", "is_deleted")
    list_filter = ("is_deleted",)
    search_fields = ("category_code", "name")

