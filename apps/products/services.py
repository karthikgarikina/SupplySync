from django.core.cache import cache

from apps.categories.models import Category
from apps.inventory.models import Inventory
from apps.products.models import Product
from core import constants
from core.exceptions import DuplicateResourceException, ResourceNotFoundException
from core.utils import random_upper_code


def _invalidate_product_cache(product_id=None):
    cache.delete(constants.CACHE_KEY_PRODUCTS_LIST)
    if product_id:
        cache.delete(constants.CACHE_KEY_PRODUCTS_DETAIL.format(id=product_id))


def _generate_sku(category):
    while True:
        sku = (
            f"{constants.CODE_PREFIX_SKU}-{category.category_code}-"
            f"{random_upper_code(constants.SKU_RANDOM_LENGTH)}"
        )
        if not Product.all_objects.filter(sku=sku).exists():
            return sku


def create_product(data: dict) -> Product:
    """Create a product with an auto-generated SKU when needed."""
    category_id = data.pop("category_id")
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist as exc:
        raise ResourceNotFoundException("Category not found.") from exc
    sku = data.get("sku") or _generate_sku(category)
    if Product.all_objects.filter(sku=sku).exists():
        raise DuplicateResourceException("SKU already exists.", code=constants.ERROR_DUPLICATE_RESOURCE)
    product = Product.objects.create(**{**data, "sku": sku, "category": category})
    _invalidate_product_cache(product.id)
    return product


def list_products(queryset):
    """Return the supplied filtered product queryset."""
    return queryset.order_by("id")


def get_product_with_inventory(product_id: int) -> dict:
    """Return product detail with inventory grouped by warehouse."""
    cache_key = constants.CACHE_KEY_PRODUCTS_DETAIL.format(id=product_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist as exc:
        raise ResourceNotFoundException("Product not found.") from exc
    inventory_rows = Inventory.objects.filter(product=product).select_related("warehouse").order_by("warehouse_id")
    result = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "unit_price": product.unit_price,
        "unit_of_measure": product.unit_of_measure,
        "reorder_level": product.reorder_level,
        "is_active": product.is_active,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "inventory_by_warehouse": [
            {
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse.name,
                "quantity_available": row.quantity_available,
                "quantity_reserved": row.quantity_reserved,
            }
            for row in inventory_rows
        ],
    }
    cache.set(cache_key, result, timeout=constants.PRODUCT_CACHE_TTL)
    return result

