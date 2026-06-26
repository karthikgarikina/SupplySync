import pytest

from apps.inventory.models import InventoryTransaction, TransactionType
from apps.sales_orders.models import SalesOrderStatus
from apps.sales_orders.services import cancel_sales_order, create_sales_order, dispatch_sales_order
from core.exceptions import InsufficientInventoryException, InvalidOperationException


def _sales_order_data(sample_inventory, quantity=5):
    return {
        "customer_name": "Client",
        "customer_email": "client@supplysync.local",
        "customer_phone": "8888888888",
        "shipping_address": "Client Address",
        "warehouse_id": sample_inventory.warehouse_id,
        "items": [
            {
                "product_id": sample_inventory.product_id,
                "quantity": quantity,
                "unit_price": sample_inventory.product.unit_price,
            }
        ],
    }


def test_create_sales_order_reserves_inventory_on_creation(db, sample_inventory, staff_user):
    create_sales_order(_sales_order_data(sample_inventory), staff_user.id)
    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == 95
    assert sample_inventory.quantity_reserved == 5


def test_create_sales_order_raises_exception_when_insufficient_stock(db, sample_inventory, staff_user):
    with pytest.raises(InsufficientInventoryException):
        create_sales_order(_sales_order_data(sample_inventory, quantity=500), staff_user.id)


def test_create_sales_order_dispatches_celery_task_on_success(db, sample_inventory, staff_user, mocker, django_capture_on_commit_callbacks):
    mocked_delay = mocker.patch("apps.sales_orders.services.process_sales_order_created_event.delay")
    with django_capture_on_commit_callbacks(execute=True):
        create_sales_order(_sales_order_data(sample_inventory), staff_user.id)
    mocked_delay.assert_called_once()


def test_cancel_sales_order_releases_reserved_inventory(db, sample_inventory, staff_user):
    sales_order = create_sales_order(_sales_order_data(sample_inventory), staff_user.id)
    cancel_sales_order(sales_order.id, "client changed mind")
    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == 100
    assert sample_inventory.quantity_reserved == 0


def test_cancel_sales_order_raises_exception_when_order_is_already_dispatched(db, sample_inventory, staff_user):
    sales_order = create_sales_order(_sales_order_data(sample_inventory), staff_user.id)
    dispatch_sales_order(sales_order.id)
    with pytest.raises(InvalidOperationException):
        cancel_sales_order(sales_order.id, "too late")


def test_dispatch_sales_order_creates_outbound_transactions_for_all_items(db, sample_inventory, staff_user):
    sales_order = create_sales_order(_sales_order_data(sample_inventory), staff_user.id)
    dispatch_sales_order(sales_order.id)
    sample_inventory.refresh_from_db()
    sales_order.refresh_from_db()
    assert sample_inventory.quantity_reserved == 0
    assert sales_order.status == SalesOrderStatus.DISPATCHED
    assert InventoryTransaction.objects.filter(transaction_type=TransactionType.OUTBOUND).count() == 1
