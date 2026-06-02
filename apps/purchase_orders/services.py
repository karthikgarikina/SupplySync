from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import TransactionType
from apps.inventory.services import adjust_inventory
from apps.products.models import Product
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from apps.purchase_orders.tasks import process_purchase_order_received_event
from apps.suppliers.models import Supplier
from apps.warehouses.models import Warehouse
from core import constants
from core.exceptions import BusinessPermissionException, InvalidOperationException, ResourceNotFoundException


def _get_purchase_order(po_id):
    try:
        return PurchaseOrder.objects.get(id=po_id)
    except PurchaseOrder.DoesNotExist as exc:
        raise ResourceNotFoundException("Purchase order not found.") from exc


def _get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist as exc:
        raise ResourceNotFoundException("User not found.") from exc


def _generate_po_number():
    today = timezone.localdate().strftime(constants.PO_DATE_FORMAT)
    key = constants.CACHE_KEY_PO_SEQUENCE.format(date=today)
    cache.add(key, 0, timeout=constants.PO_SEQUENCE_TTL)
    sequence = cache.incr(key)
    return f"{constants.CODE_PREFIX_PURCHASE_ORDER}-{today}-{sequence:04d}"


def _create_items(purchase_order, items):
    total_amount = Decimal("0.00")
    for item in items:
        try:
            product = Product.objects.get(id=item["product_id"])
        except Product.DoesNotExist as exc:
            raise ResourceNotFoundException("Product not found.") from exc
        total_price = Decimal(item["quantity_ordered"]) * item["unit_price"]
        total_amount += total_price
        PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=item["quantity_ordered"],
            unit_price=item["unit_price"],
            total_price=total_price,
        )
    purchase_order.total_amount = total_amount
    purchase_order.save(update_fields=["total_amount", "updated_at"])


def create_purchase_order(data: dict, created_by_user_id: int) -> PurchaseOrder:
    """Create a draft purchase order with a Redis-backed daily sequence number."""
    items = data.pop("items", [])
    try:
        supplier = Supplier.objects.get(id=data.pop("supplier_id"))
        warehouse = Warehouse.objects.get(id=data.pop("warehouse_id"))
    except Supplier.DoesNotExist as exc:
        raise ResourceNotFoundException("Supplier not found.") from exc
    except Warehouse.DoesNotExist as exc:
        raise ResourceNotFoundException("Warehouse not found.") from exc
    created_by = _get_user(created_by_user_id)
    with transaction.atomic():
        purchase_order = PurchaseOrder.objects.create(
            po_number=_generate_po_number(),
            supplier=supplier,
            warehouse=warehouse,
            status=PurchaseOrderStatus.DRAFT,
            created_by=created_by,
            expected_delivery_date=data.get("expected_delivery_date"),
            notes=data.get("notes"),
        )
        _create_items(purchase_order, items)
    return purchase_order


def list_purchase_orders():
    """Return purchase orders ordered by newest first."""
    return PurchaseOrder.objects.prefetch_related("items").order_by("-id")


def submit_purchase_order(po_id: int) -> PurchaseOrder:
    """Move a draft purchase order to pending approval."""
    purchase_order = _get_purchase_order(po_id)
    if not purchase_order.items.exists():
        raise InvalidOperationException("Purchase order has no items.", code=constants.ERROR_PO_HAS_NO_ITEMS)
    if purchase_order.status != PurchaseOrderStatus.DRAFT:
        raise InvalidOperationException("Purchase order cannot be submitted.", code=constants.ERROR_INVALID_OPERATION)
    purchase_order.status = PurchaseOrderStatus.PENDING_APPROVAL
    purchase_order.save(update_fields=["status", "updated_at"])
    return purchase_order


def approve_purchase_order(po_id: int, approved_by_user_id: int) -> PurchaseOrder:
    """Approve a pending purchase order while preventing creator self-approval."""
    purchase_order = _get_purchase_order(po_id)
    approved_by = _get_user(approved_by_user_id)
    if purchase_order.created_by_id == approved_by.id:
        raise BusinessPermissionException(
            "Self approval is not allowed.",
            code=constants.ERROR_SELF_APPROVAL_NOT_ALLOWED,
        )
    if purchase_order.status != PurchaseOrderStatus.PENDING_APPROVAL:
        raise InvalidOperationException("Purchase order is not pending approval.", code=constants.ERROR_INVALID_OPERATION)
    purchase_order.status = PurchaseOrderStatus.APPROVED
    purchase_order.approved_by = approved_by
    purchase_order.save(update_fields=["status", "approved_by", "updated_at"])
    return purchase_order


def receive_purchase_order(po_id: int, data: dict, performed_by_user_id: int) -> PurchaseOrder:
    """Receive purchase order items and post inbound inventory adjustments."""
    purchase_order = _get_purchase_order(po_id)
    with transaction.atomic():
        for received_item in data["items"]:
            try:
                item = purchase_order.items.select_for_update().get(id=received_item["po_item_id"])
            except PurchaseOrderItem.DoesNotExist as exc:
                raise ResourceNotFoundException("Purchase order item not found.") from exc
            remaining = item.quantity_ordered - item.quantity_received
            if received_item["quantity_received"] > remaining:
                raise InvalidOperationException("Received quantity exceeds remaining quantity.", code=constants.ERROR_INVALID_OPERATION)
            item.quantity_received += received_item["quantity_received"]
            item.save(update_fields=["quantity_received", "updated_at"])
            adjust_inventory(
                {
                    "product_id": item.product_id,
                    "warehouse_id": purchase_order.warehouse_id,
                    "transaction_type": TransactionType.INBOUND,
                    "quantity": received_item["quantity_received"],
                    "notes": purchase_order.po_number,
                },
                performed_by_user_id,
            )
        purchase_order.actual_delivery_date = data.get("actual_delivery_date") or timezone.localdate()
        all_received = all(item.quantity_received >= item.quantity_ordered for item in purchase_order.items.all())
        purchase_order.status = PurchaseOrderStatus.RECEIVED if all_received else PurchaseOrderStatus.PARTIALLY_RECEIVED
        purchase_order.save(update_fields=["actual_delivery_date", "status", "updated_at"])
    process_purchase_order_received_event.delay(purchase_order.id, performed_by_user_id)
    return purchase_order


def cancel_purchase_order(po_id: int, reason: str) -> PurchaseOrder:
    """Cancel a purchase order when its status permits cancellation."""
    purchase_order = _get_purchase_order(po_id)
    allowed_statuses = {
        PurchaseOrderStatus.DRAFT,
        PurchaseOrderStatus.PENDING_APPROVAL,
        PurchaseOrderStatus.APPROVED,
    }
    if purchase_order.status not in allowed_statuses:
        raise InvalidOperationException(
            "Purchase order cancellation is not allowed.",
            code=constants.ERROR_PO_CANCELLATION_NOT_ALLOWED,
        )
    purchase_order.status = PurchaseOrderStatus.CANCELLED
    if reason:
        purchase_order.notes = f"{purchase_order.notes or ''}\nCancellation reason: {reason}".strip()
    purchase_order.save(update_fields=["status", "notes", "updated_at"])
    return purchase_order

