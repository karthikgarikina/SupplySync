from django.conf import settings
from django.db import models

from core.models import BaseModel


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    ORDERED = "ORDERED", "Ordered"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
    RECEIVED = "RECEIVED", "Received"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrder(BaseModel):
    po_number = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT)
    warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.PROTECT)
    status = models.CharField(max_length=30, choices=PurchaseOrderStatus.choices)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchase_orders",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_purchase_orders",
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "purchase_orders"

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    quantity_ordered = models.IntegerField()
    quantity_received = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "purchase_order_items"

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.sku}"

