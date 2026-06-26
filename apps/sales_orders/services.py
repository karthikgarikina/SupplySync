from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Inventory, InventoryTransaction, TransactionType
from apps.products.models import Product
from apps.sales_orders.models import SalesOrder, SalesOrderItem, SalesOrderStatus
from apps.sales_orders.tasks import process_sales_order_cancelled_event, process_sales_order_created_event
from apps.warehouses.models import Warehouse
from core import constants
from core.exceptions import InsufficientInventoryException, InvalidOperationException, ResourceNotFoundException
from core.utils import random_upper_code


def _get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist as exc:
        raise ResourceNotFoundException("User not found.") from exc


def _get_sales_order(so_id):
    try:
        return SalesOrder.objects.prefetch_related("items").get(id=so_id)
    except SalesOrder.DoesNotExist as exc:
        raise ResourceNotFoundException("Sales order not found.") from exc


def _generate_order_number():
    today = timezone.localdate().strftime(constants.PO_DATE_FORMAT)
    return f"{constants.CODE_PREFIX_SALES_ORDER}-{today}-{random_upper_code(constants.SHORT_CODE_LENGTH)}"


def _get_product_map(items):
    product_ids = [item["product_id"] for item in items]
    products = {product.id: product for product in Product.objects.filter(id__in=product_ids)}
    missing = set(product_ids) - set(products)
    if missing:
        raise ResourceNotFoundException("Product not found.")
    return products


def create_sales_order(data: dict, created_by_user_id: int) -> SalesOrder:
    """Create a sales order and reserve inventory with row-level locks."""
    items = data.pop("items")
    try:
        warehouse = Warehouse.objects.get(id=data.pop("warehouse_id"))
    except Warehouse.DoesNotExist as exc:
        raise ResourceNotFoundException("Warehouse not found.") from exc
    created_by = _get_user(created_by_user_id)
    products = _get_product_map(items)

    with transaction.atomic():
        inventory_rows = {
            row.product_id: row
            for row in Inventory.objects.select_for_update().filter(
                warehouse=warehouse,
                product_id__in=products.keys(),
            )
        }
        short_items = []
        for item in items:
            inventory = inventory_rows.get(item["product_id"])
            available_quantity = inventory.quantity_available if inventory else 0
            if available_quantity < item["quantity"]:
                product = products[item["product_id"]]
                short_items.append(
                    {
                        "sku": product.sku,
                        "requested_quantity": item["quantity"],
                        "available_quantity": available_quantity,
                    }
                )
        if short_items:
            raise InsufficientInventoryException(
                "Insufficient stock for order.",
                code=constants.ERROR_INSUFFICIENT_STOCK_FOR_ORDER,
                extra_data={"short_items": short_items},
            )
        sales_order = SalesOrder.objects.create(
            order_number=_generate_order_number(),
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            customer_phone=data["customer_phone"],
            shipping_address=data["shipping_address"],
            warehouse=warehouse,
            status=SalesOrderStatus.CONFIRMED,
            created_by=created_by,
            notes=data.get("notes"),
        )
        total_amount = Decimal("0.00")
        for item in items:
            inventory = inventory_rows[item["product_id"]]
            inventory.quantity_available -= item["quantity"]
            inventory.quantity_reserved += item["quantity"]
            inventory.save()
            total_price = Decimal(item["quantity"]) * item["unit_price"]
            total_amount += total_price
            SalesOrderItem.objects.create(
                sales_order=sales_order,
                product=products[item["product_id"]],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                total_price=total_price,
            )
        sales_order.total_amount = total_amount
        sales_order.save(update_fields=["total_amount", "updated_at"])

    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_REPORTS_DASHBOARD))
    transaction.on_commit(lambda: process_sales_order_created_event.delay(sales_order.id, created_by_user_id))
    return sales_order


def list_sales_orders():
    """Return sales orders ordered by newest first."""
    return SalesOrder.objects.prefetch_related("items").order_by("-id")


def dispatch_sales_order(so_id: int) -> SalesOrder:
    """Dispatch a sales order and convert reserved stock to outbound transactions."""
    sales_order = _get_sales_order(so_id)
    if sales_order.status not in {SalesOrderStatus.CONFIRMED, SalesOrderStatus.PROCESSING}:
        raise InvalidOperationException("Sales order cannot be dispatched.", code=constants.ERROR_INVALID_OPERATION)
    with transaction.atomic():
        sales_order = SalesOrder.objects.select_for_update().get(id=so_id)
        for item in sales_order.items.select_related("product").all():
            inventory = Inventory.objects.select_for_update().get(product=item.product, warehouse=sales_order.warehouse)
            if inventory.quantity_reserved < item.quantity:
                raise InvalidOperationException("Reserved quantity is insufficient.", code=constants.ERROR_INVALID_OPERATION)
            inventory.quantity_reserved -= item.quantity
            inventory.save()
            InventoryTransaction.objects.create(
                product=item.product,
                warehouse=sales_order.warehouse,
                transaction_type=TransactionType.OUTBOUND,
                quantity=item.quantity,
                reference_id=sales_order.order_number,
                performed_by=sales_order.created_by,
                notes=sales_order.order_number,
            )
        sales_order.status = SalesOrderStatus.DISPATCHED
        sales_order.dispatched_at = timezone.now()
        sales_order.save(update_fields=["status", "dispatched_at", "updated_at"])
    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_REPORTS_DASHBOARD))
    return sales_order


def deliver_sales_order(so_id: int) -> SalesOrder:
    """Mark a dispatched sales order as delivered."""
    sales_order = _get_sales_order(so_id)
    if sales_order.status != SalesOrderStatus.DISPATCHED:
        raise InvalidOperationException("Only dispatched orders can be delivered.", code=constants.ERROR_INVALID_OPERATION)
    sales_order.status = SalesOrderStatus.DELIVERED
    sales_order.delivered_at = timezone.now()
    sales_order.save(update_fields=["status", "delivered_at", "updated_at"])
    cache.delete(constants.CACHE_KEY_REPORTS_DASHBOARD)
    return sales_order


def cancel_sales_order(so_id: int, reason: str) -> SalesOrder:
    """Cancel a pending or confirmed order and release reserved inventory."""
    sales_order = _get_sales_order(so_id)
    if sales_order.status not in {SalesOrderStatus.PENDING, SalesOrderStatus.CONFIRMED}:
        raise InvalidOperationException(
            "Sales order cancellation is not allowed.",
            code=constants.ERROR_SO_CANCELLATION_NOT_ALLOWED,
        )
    with transaction.atomic():
        sales_order = SalesOrder.objects.select_for_update().get(id=so_id)
        for item in sales_order.items.all():
            inventory = Inventory.objects.select_for_update().get(product=item.product, warehouse=sales_order.warehouse)
            inventory.quantity_reserved -= item.quantity
            inventory.quantity_available += item.quantity
            inventory.save()
        sales_order.status = SalesOrderStatus.CANCELLED
        if reason:
            sales_order.notes = f"{sales_order.notes or ''}\nCancellation reason: {reason}".strip()
        sales_order.save(update_fields=["status", "notes", "updated_at"])
    transaction.on_commit(lambda: cache.delete(constants.CACHE_KEY_REPORTS_DASHBOARD))
    transaction.on_commit(lambda: process_sales_order_cancelled_event.delay(sales_order.id))
    return sales_order
