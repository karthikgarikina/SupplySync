from django.core.cache import cache

from apps.suppliers.models import Supplier
from core import constants
from core.exceptions import DuplicateResourceException, ResourceNotFoundException
from core.utils import random_upper_code


def _invalidate_supplier_cache(supplier_id=None):
    if supplier_id:
        cache.delete(constants.CACHE_KEY_SUPPLIERS_DETAIL.format(id=supplier_id))


def _generate_supplier_code():
    while True:
        code = f"{constants.CODE_PREFIX_SUPPLIER}-{random_upper_code(constants.SHORT_CODE_LENGTH)}"
        if not Supplier.all_objects.filter(supplier_code=code).exists():
            return code


def create_supplier(data: dict) -> Supplier:
    """Create a supplier and generate supplier_code when absent."""
    code = data.get("supplier_code") or _generate_supplier_code()
    if Supplier.all_objects.filter(supplier_code=code).exists():
        raise DuplicateResourceException("Supplier code already exists.", code=constants.ERROR_DUPLICATE_RESOURCE)
    supplier = Supplier.objects.create(**{**data, "supplier_code": code})
    _invalidate_supplier_cache(supplier.id)
    return supplier


def update_supplier(supplier_id: int, data: dict) -> Supplier:
    """Update a supplier record."""
    supplier = get_supplier_by_id(supplier_id)
    for field, value in data.items():
        setattr(supplier, field, value)
    supplier.save()
    _invalidate_supplier_cache(supplier.id)
    return supplier


def get_supplier_by_id(supplier_id: int) -> Supplier:
    """Return a supplier by primary key."""
    cache_key = constants.CACHE_KEY_SUPPLIERS_DETAIL.format(id=supplier_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        supplier = Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist as exc:
        raise ResourceNotFoundException("Supplier not found.") from exc
    cache.set(cache_key, supplier, timeout=constants.SUPPLIER_CACHE_TTL)
    return supplier


def list_suppliers(filters: dict, page: int, page_size: int):
    """Return suppliers filtered by active flag and search text."""
    queryset = Supplier.objects.order_by("id")
    if filters.get("is_active") in {"true", "True", True}:
        queryset = queryset.filter(is_active=True)
    if filters.get("city"):
        queryset = queryset.filter(city=filters["city"])
    return queryset


def delete_supplier(supplier_id: int) -> None:
    """Soft delete a supplier by primary key."""
    supplier = get_supplier_by_id(supplier_id)
    supplier.delete()
    _invalidate_supplier_cache(supplier_id)

