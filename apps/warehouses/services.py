from django.core.cache import cache
from django.db.models import Sum

from apps.inventory.models import Inventory
from apps.warehouses.models import Warehouse
from core import constants
from core.exceptions import DuplicateResourceException, InvalidOperationException, ResourceNotFoundException
from core.utils import random_upper_code


def _invalidate_warehouse_cache(warehouse_id=None):
    cache.delete(constants.CACHE_KEY_WAREHOUSES_LIST)
    if warehouse_id:
        cache.delete(constants.CACHE_KEY_WAREHOUSES_DETAIL.format(id=warehouse_id))


def _generate_warehouse_code():
    while True:
        code = f"{constants.CODE_PREFIX_WAREHOUSE}-{random_upper_code(constants.SHORT_CODE_LENGTH)}"
        if not Warehouse.all_objects.filter(warehouse_code=code).exists():
            return code


def create_warehouse(data: dict) -> Warehouse:
    """Create a warehouse with an auto-generated code when needed."""
    code = data.get("warehouse_code") or _generate_warehouse_code()
    if Warehouse.all_objects.filter(warehouse_code=code).exists():
        raise DuplicateResourceException("Warehouse code already exists.", code=constants.ERROR_DUPLICATE_RESOURCE)
    warehouse = Warehouse.objects.create(**{**data, "warehouse_code": code})
    _invalidate_warehouse_cache(warehouse.id)
    return warehouse


def list_warehouses(filters: dict):
    """Return active warehouses filtered by city and state."""
    if not filters:
        cached = cache.get(constants.CACHE_KEY_WAREHOUSES_LIST)
        if cached is not None:
            return cached
    queryset = Warehouse.objects.filter(is_active=True).order_by("id")
    if filters.get("city"):
        queryset = queryset.filter(city=filters["city"])
    if filters.get("state"):
        queryset = queryset.filter(state=filters["state"])
    if not filters:
        cache.set(constants.CACHE_KEY_WAREHOUSES_LIST, queryset, timeout=constants.WAREHOUSE_CACHE_TTL)
    return queryset


def get_warehouse_with_summary(warehouse_id: int) -> dict:
    """Return a warehouse and its inventory summary."""
    cache_key = constants.CACHE_KEY_WAREHOUSES_DETAIL.format(id=warehouse_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
    except Warehouse.DoesNotExist as exc:
        raise ResourceNotFoundException("Warehouse not found.") from exc
    inventory = Inventory.objects.filter(warehouse=warehouse)
    result = {
        "id": warehouse.id,
        "warehouse_code": warehouse.warehouse_code,
        "name": warehouse.name,
        "location": warehouse.location,
        "city": warehouse.city,
        "state": warehouse.state,
        "pincode": warehouse.pincode,
        "capacity": warehouse.capacity,
        "is_active": warehouse.is_active,
        "created_at": warehouse.created_at,
        "updated_at": warehouse.updated_at,
        "total_distinct_products": inventory.values("product_id").distinct().count(),
        "total_quantity_available": inventory.aggregate(total=Sum("quantity_available"))["total"] or 0,
    }
    cache.set(cache_key, result, timeout=constants.WAREHOUSE_CACHE_TTL)
    return result


def update_warehouse(warehouse_id: int, data: dict) -> Warehouse:
    """Update warehouse details while keeping warehouse_code immutable."""
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
    except Warehouse.DoesNotExist as exc:
        raise ResourceNotFoundException("Warehouse not found.") from exc
    if "warehouse_code" in data and data["warehouse_code"] != warehouse.warehouse_code:
        raise InvalidOperationException(
            constants.ERROR_WAREHOUSE_CODE_IMMUTABLE,
            code=constants.ERROR_WAREHOUSE_CODE_IMMUTABLE,
        )
    data.pop("warehouse_code", None)
    for field, value in data.items():
        setattr(warehouse, field, value)
    warehouse.save()
    _invalidate_warehouse_cache(warehouse.id)
    return warehouse


def delete_warehouse(warehouse_id: int) -> None:
    """Soft delete a warehouse when it has no active inventory."""
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
    except Warehouse.DoesNotExist as exc:
        raise ResourceNotFoundException("Warehouse not found.") from exc
    has_stock = Inventory.objects.filter(
        warehouse=warehouse,
        quantity_available__gt=0,
    ).exists() or Inventory.objects.filter(warehouse=warehouse, quantity_reserved__gt=0).exists()
    if has_stock:
        raise DuplicateResourceException(
            "Warehouse has active inventory.",
            code=constants.ERROR_WAREHOUSE_HAS_ACTIVE_INVENTORY,
        )
    warehouse.delete()
    _invalidate_warehouse_cache(warehouse.id)

