from django.conf import settings
from django.db import models

from core.models import BaseModel


class TransactionType(models.TextChoices):
    INBOUND = "INBOUND", "Inbound"
    OUTBOUND = "OUTBOUND", "Outbound"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"
    TRANSFER = "TRANSFER", "Transfer"
    DAMAGE_REPORT = "DAMAGE_REPORT", "Damage Report"


class Inventory(BaseModel):
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.PROTECT)
    quantity_available = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)
    quantity_damaged = models.IntegerField(default=0)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory"
        unique_together = [("product", "warehouse")]

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.warehouse_code}"


class InventoryTransaction(models.Model):
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=30, choices=TransactionType.choices)
    quantity = models.IntegerField()
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_transactions"

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.product.sku}"

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get("force_insert"):
            raise ValueError("InventoryTransaction is append-only.")
        return super().save(*args, **kwargs)

