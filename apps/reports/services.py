from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.utils import timezone

from apps.inventory.models import Inventory, InventoryTransaction, TransactionType
from apps.products.models import Product
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderStatus
from apps.sales_orders.models import SalesOrder, SalesOrderItem, SalesOrderStatus
from apps.suppliers.models import Supplier
from apps.warehouses.models import Warehouse
from core import constants


def _to_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _money(value):
    return value or Decimal("0.00")


def get_dashboard_summary() -> dict:
    """Return the cached dashboard summary."""
    cached = cache.get(constants.CACHE_KEY_REPORTS_DASHBOARD)
    if cached is not None:
        return cached
    line_value = ExpressionWrapper(
        F("quantity_available") * F("product__unit_price"),
        output_field=DecimalField(max_digits=16, decimal_places=2),
    )
    total_inventory_value = _money(
        Inventory.objects.annotate(line_value=line_value).aggregate(total=Sum("line_value"))["total"]
    )
    since = timezone.now() - timedelta(days=30)
    top_selling_products = list(
        InventoryTransaction.objects.filter(
            transaction_type=TransactionType.OUTBOUND,
            created_at__gte=since,
        )
        .values("product_id", "product__sku", "product__name")
        .annotate(total_dispatched=Sum("quantity"))
        .order_by("-total_dispatched")[:5]
    )
    recent_transactions = [
        {
            "id": row.id,
            "product_id": row.product_id,
            "sku": row.product.sku,
            "warehouse_id": row.warehouse_id,
            "warehouse_name": row.warehouse.name,
            "transaction_type": row.transaction_type,
            "quantity": row.quantity,
            "created_at": row.created_at,
        }
        for row in InventoryTransaction.objects.select_related("product", "warehouse").order_by("-created_at")[:10]
    ]
    result = {
        "total_warehouses": Warehouse.objects.filter(is_active=True).count(),
        "total_products": Product.objects.filter(is_active=True).count(),
        "total_suppliers": Supplier.objects.filter(is_active=True).count(),
        "total_inventory_value": total_inventory_value,
        "open_purchase_orders": PurchaseOrder.objects.exclude(
            status__in=[PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED]
        ).count(),
        "pending_sales_orders": SalesOrder.objects.filter(
            status__in=[SalesOrderStatus.PENDING, SalesOrderStatus.CONFIRMED, SalesOrderStatus.PROCESSING]
        ).count(),
        "low_stock_product_count": Inventory.objects.filter(quantity_available__lte=F("product__reorder_level")).count(),
        "top_selling_products": top_selling_products,
        "recent_transactions": recent_transactions,
    }
    cache.set(constants.CACHE_KEY_REPORTS_DASHBOARD, result, timeout=constants.REPORT_CACHE_TTL)
    return result


def get_inventory_valuation(warehouse_id: int = None) -> dict:
    """Return inventory valuation grouped by warehouse."""
    queryset = Inventory.objects.select_related("warehouse", "product").order_by("warehouse_id", "product_id")
    if warehouse_id:
        queryset = queryset.filter(warehouse_id=warehouse_id)
    grouped = defaultdict(lambda: {"warehouse_id": None, "warehouse_name": None, "products": [], "warehouse_total_value": Decimal("0.00")})
    grand_total = Decimal("0.00")
    for row in queryset:
        total_value = row.quantity_available * row.product.unit_price
        bucket = grouped[row.warehouse_id]
        bucket["warehouse_id"] = row.warehouse_id
        bucket["warehouse_name"] = row.warehouse.name
        bucket["products"].append(
            {
                "sku": row.product.sku,
                "product_name": row.product.name,
                "quantity_available": row.quantity_available,
                "unit_price": row.product.unit_price,
                "total_value": total_value,
            }
        )
        bucket["warehouse_total_value"] += total_value
        grand_total += total_value
    return {
        "grand_total_value": grand_total,
        "warehouses": list(grouped.values()),
    }


def get_purchase_order_summary(start_date, end_date, supplier_id=None, status=None) -> dict:
    """Return purchase order summary metrics with optional filters."""
    queryset = PurchaseOrder.objects.all()
    start_date = _to_date(start_date)
    end_date = _to_date(end_date)
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)
    if status:
        queryset = queryset.filter(status=status)
    breakdown = list(
        queryset.values("status")
        .annotate(count=Count("id"), total_value=Sum("total_amount"))
        .order_by("status")
    )
    top_suppliers = list(
        queryset.values("supplier_id", "supplier__name")
        .annotate(total_value=Sum("total_amount"))
        .order_by("-total_value")[:5]
    )
    return {
        "total_orders": queryset.count(),
        "total_value": _money(queryset.aggregate(total=Sum("total_amount"))["total"]),
        "breakdown_by_status": breakdown,
        "top_suppliers": top_suppliers,
    }


def get_sales_order_summary(start_date, end_date, warehouse_id=None, status=None) -> dict:
    """Return sales order summary metrics with revenue for delivered orders only."""
    queryset = SalesOrder.objects.all()
    start_date = _to_date(start_date)
    end_date = _to_date(end_date)
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    if warehouse_id:
        queryset = queryset.filter(warehouse_id=warehouse_id)
    if status:
        queryset = queryset.filter(status=status)
    delivered = queryset.filter(status=SalesOrderStatus.DELIVERED)
    total_revenue = _money(delivered.aggregate(total=Sum("total_amount"))["total"])
    delivered_count = delivered.count()
    breakdown = list(
        queryset.values("status")
        .annotate(count=Count("id"), total_value=Sum("total_amount"))
        .order_by("status")
    )
    item_filter = Q(sales_order__in=queryset)
    top_products = list(
        SalesOrderItem.objects.filter(item_filter)
        .values("product_id", "product__sku", "product__name")
        .annotate(total_revenue=Sum("total_price"))
        .order_by("-total_revenue")[:5]
    )
    return {
        "total_orders": queryset.count(),
        "total_revenue": total_revenue,
        "average_order_value": (total_revenue / delivered_count) if delivered_count else Decimal("0.00"),
        "breakdown_by_status": breakdown,
        "top_products_by_revenue": top_products,
    }

