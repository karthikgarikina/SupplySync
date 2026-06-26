import logging
import uuid

from django.core.cache import cache
from django.db import transaction
from django.db.models import F

from apps.accounts.models import User
from apps.inventory.models import Inventory, InventoryTransaction, TransactionType
from apps.inventory.tasks import process_inventory_transfer_event, process_inventory_updated_event
from apps.products.models import Product
from apps.warehouses.models import Warehouse
from core import constants
from core.exceptions import InsufficientInventoryException, InvalidOperationException, ResourceNotFoundException

logger = logging.getLogger(__name__)


def _get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist as exc:
        raise ResourceNotFoundException("User not found.") from exc


def _get_product(product_id):
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist as exc:
        raise ResourceNotFoundException("Product not found.") from exc


def _get_warehouse(warehouse_id):
    try:
        return Warehouse.objects.get(id=warehouse_id)
    except Warehouse.DoesNotExist as exc:
        raise ResourceNotFoundException("Warehouse not found.") from exc


def _get_locked_inventory(product, warehouse):
    inventory, _ = Inventory.objects.select_for_update().get_or_create(product=product, warehouse=warehouse)
    return inventory


def _raise_insufficient(message="Insufficient inventory."):
    raise InsufficientInventoryException(message, code=constants.ERROR_INSUFFICIENT_INVENTORY)


def adjust_inventory(data: dict, performed_by_user_id: int) -> InventoryTransaction:
    """Adjust inventory atomically and create an immutable transaction record."""
    product = _get_product(data["product_id"])
    warehouse = _get_warehouse(data["warehouse_id"])
    performed_by = _get_user(performed_by_user_id)
    transaction_type = data["transaction_type"]
    quantity = data["quantity"]

    with transaction.atomic():
        inventory = _get_locked_inventory(product, warehouse)
        if transaction_type == TransactionType.INBOUND:
            inventory.quantity_available += quantity
        elif transaction_type == TransactionType.OUTBOUND:
            if inventory.quantity_available < quantity:
                _raise_insufficient()
            inventory.quantity_available -= quantity
        elif transaction_type == TransactionType.DAMAGE_REPORT:
            if inventory.quantity_available < quantity:
                _raise_insufficient()
            inventory.quantity_available -= quantity
            inventory.quantity_damaged += quantity
        elif transaction_type == TransactionType.ADJUSTMENT:
            if inventory.quantity_available + quantity < 0:
                _raise_insufficient()
            inventory.quantity_available += quantity
        else:
            raise InvalidOperationException("Unsupported transaction type.", code=constants.ERROR_INVALID_OPERATION)
        inventory.save()
        inventory_transaction = InventoryTransaction.objects.create(
            product=product,
            warehouse=warehouse,
            transaction_type=transaction_type,
            quantity=quantity,
            performed_by=performed_by,
            notes=data.get("notes"),
        )

    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_INVENTORY_LOW_STOCK))
    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_REPORTS_DASHBOARD))
    transaction.on_commit(lambda: process_inventory_updated_event.delay(product.id, warehouse.id, transaction_type, quantity))
    return inventory_transaction


def transfer_inventory(data: dict, performed_by_user_id: int) -> dict:
    """Transfer stock between warehouses with row-level locks on inventory rows."""
    product = _get_product(data["product_id"])
    source_warehouse = _get_warehouse(data["source_warehouse_id"])
    destination_warehouse = _get_warehouse(data["destination_warehouse_id"])
    performed_by = _get_user(performed_by_user_id)
    quantity = data["quantity"]
    reference_id = f"{constants.CODE_PREFIX_TRANSFER}-{uuid.uuid4().hex[:8].upper()}"

    with transaction.atomic():
        source_inventory = _get_locked_inventory(product, source_warehouse)
        destination_inventory = _get_locked_inventory(product, destination_warehouse)
        if source_inventory.quantity_available < quantity:
            _raise_insufficient()
        source_inventory.quantity_available -= quantity
        destination_inventory.quantity_available += quantity
        source_inventory.save()
        destination_inventory.save()
        source_transaction = InventoryTransaction.objects.create(
            product=product,
            warehouse=source_warehouse,
            transaction_type=TransactionType.OUTBOUND,
            quantity=quantity,
            reference_id=reference_id,
            performed_by=performed_by,
            notes=data.get("notes"),
        )
        destination_transaction = InventoryTransaction.objects.create(
            product=product,
            warehouse=destination_warehouse,
            transaction_type=TransactionType.INBOUND,
            quantity=quantity,
            reference_id=reference_id,
            performed_by=performed_by,
            notes=data.get("notes"),
        )

    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_INVENTORY_LOW_STOCK))
    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_REPORTS_DASHBOARD))
    transaction.on_commit(lambda: process_inventory_transfer_event.delay(product.id, source_warehouse.id, destination_warehouse.id, quantity))
    return {
        "reference_id": reference_id,
        "source_transaction": source_transaction,
        "destination_transaction": destination_transaction,
    }


def get_low_stock_alerts() -> list:
    """Return and cache inventory rows at or below product reorder level."""
    cached = cache.get(constants.CACHE_KEY_INVENTORY_LOW_STOCK)
    if cached is not None:
        return cached
    rows = (
        Inventory.objects.select_related("product", "warehouse")
        .filter(quantity_available__lte=F("product__reorder_level"))
        .order_by("product_id", "warehouse_id")
    )
    alerts = [
        {
            "product_id": row.product_id,
            "sku": row.product.sku,
            "product_name": row.product.name,
            "warehouse_id": row.warehouse_id,
            "warehouse_name": row.warehouse.name,
            "quantity_available": row.quantity_available,
            "reorder_level": row.product.reorder_level,
            "deficit": row.product.reorder_level - row.quantity_available,
        }
        for row in rows
    ]
    cache.set(constants.CACHE_KEY_INVENTORY_LOW_STOCK, alerts, timeout=constants.LOW_STOCK_CACHE_TTL)
    return alerts


def check_and_publish_low_stock_alert(product_id: int, warehouse_id: int) -> None:
    """Log a low-stock warning and invalidate the low-stock cache when below reorder level."""
    try:
        inventory = Inventory.objects.select_related("product", "warehouse").get(
            product_id=product_id,
            warehouse_id=warehouse_id,
        )
    except Inventory.DoesNotExist:
        return
    if inventory.quantity_available <= inventory.product.reorder_level:
        logger.warning(
            constants.LOW_STOCK_LOG,
            inventory.product.sku,
            inventory.warehouse.warehouse_code,
            inventory.quantity_available,
            inventory.product.reorder_level,
        )
        cache.delete(constants.CACHE_KEY_INVENTORY_LOW_STOCK)


def get_warehouse_inventory(warehouse_id: int):
    """Return inventory snapshot rows for a warehouse."""
    _get_warehouse(warehouse_id)
    rows = Inventory.objects.select_related("product", "warehouse").filter(warehouse_id=warehouse_id).order_by("id")
    return [
        {
            "id": row.id,
            "product_id": row.product_id,
            "sku": row.product.sku,
            "product_name": row.product.name,
            "warehouse_id": row.warehouse_id,
            "warehouse_name": row.warehouse.name,
            "quantity_available": row.quantity_available,
            "quantity_reserved": row.quantity_reserved,
            "quantity_damaged": row.quantity_damaged,
            "last_updated_at": row.last_updated_at,
        }
        for row in rows
    ]
