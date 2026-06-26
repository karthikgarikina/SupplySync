import pytest

from apps.inventory.models import Inventory, InventoryTransaction, TransactionType
from apps.inventory.services import adjust_inventory, get_low_stock_alerts, transfer_inventory
from apps.warehouses.models import Warehouse
from core.exceptions import InsufficientInventoryException


def test_adjust_inventory_creates_transaction_record_when_inbound(db, sample_inventory, staff_user):
    transaction = adjust_inventory(
        {
            "product_id": sample_inventory.product_id,
            "warehouse_id": sample_inventory.warehouse_id,
            "transaction_type": TransactionType.INBOUND,
            "quantity": 10,
            "notes": "received",
        },
        staff_user.id,
    )

    sample_inventory.refresh_from_db()
    assert transaction.id is not None
    assert sample_inventory.quantity_available == 110
    assert InventoryTransaction.objects.count() == 1


def test_adjust_inventory_raises_exception_when_outbound_exceeds_available(db, sample_inventory, staff_user):
    with pytest.raises(InsufficientInventoryException):
        adjust_inventory(
            {
                "product_id": sample_inventory.product_id,
                "warehouse_id": sample_inventory.warehouse_id,
                "transaction_type": TransactionType.OUTBOUND,
                "quantity": 1000,
            },
            staff_user.id,
        )


def test_adjust_inventory_dispatches_celery_task_on_success(db, sample_inventory, staff_user, mocker, django_capture_on_commit_callbacks):
    mocked_delay = mocker.patch("apps.inventory.services.process_inventory_updated_event.delay")
    with django_capture_on_commit_callbacks(execute=True):
        adjust_inventory(
            {
                "product_id": sample_inventory.product_id,
                "warehouse_id": sample_inventory.warehouse_id,
                "transaction_type": TransactionType.INBOUND,
                "quantity": 1,
            },
            staff_user.id,
        )
    mocked_delay.assert_called_once()


def test_transfer_inventory_deducts_from_source_and_adds_to_destination(db, sample_inventory, sample_warehouse, staff_user):
    destination = Warehouse.objects.create(
        warehouse_code="WH-DEST01",
        name="Destination",
        location="Second Road",
        city="Mysuru",
        state="Karnataka",
        pincode="570001",
        capacity=5000,
    )
    transfer_inventory(
        {
            "product_id": sample_inventory.product_id,
            "source_warehouse_id": sample_inventory.warehouse_id,
            "destination_warehouse_id": destination.id,
            "quantity": 25,
        },
        staff_user.id,
    )
    sample_inventory.refresh_from_db()
    destination_inventory = Inventory.objects.get(product=sample_inventory.product, warehouse=destination)
    assert sample_inventory.quantity_available == 75
    assert destination_inventory.quantity_available == 25


def test_transfer_inventory_raises_exception_when_source_has_insufficient_stock(db, sample_inventory, staff_user):
    destination = Warehouse.objects.create(
        warehouse_code="WH-DEST02",
        name="Destination Two",
        location="Third Road",
        city="Hubballi",
        state="Karnataka",
        pincode="580001",
        capacity=5000,
    )
    with pytest.raises(InsufficientInventoryException):
        transfer_inventory(
            {
                "product_id": sample_inventory.product_id,
                "source_warehouse_id": sample_inventory.warehouse_id,
                "destination_warehouse_id": destination.id,
                "quantity": 1000,
            },
            staff_user.id,
        )


def test_get_low_stock_alerts_returns_products_below_reorder_level(db, sample_inventory):
    sample_inventory.quantity_available = 5
    sample_inventory.save()
    alerts = get_low_stock_alerts()
    assert alerts[0]["product_id"] == sample_inventory.product_id
    assert alerts[0]["deficit"] == 5
