import re

import pytest

from apps.inventory.models import Inventory
from apps.purchase_orders.models import PurchaseOrderStatus
from apps.purchase_orders.services import approve_purchase_order, cancel_purchase_order, create_purchase_order, receive_purchase_order, submit_purchase_order
from core.exceptions import BusinessPermissionException, InvalidOperationException


def _purchase_order_data(sample_supplier, sample_warehouse, sample_product, quantity=10):
    return {
        "supplier_id": sample_supplier.id,
        "warehouse_id": sample_warehouse.id,
        "items": [
            {
                "product_id": sample_product.id,
                "quantity_ordered": quantity,
                "unit_price": sample_product.unit_price,
            }
        ],
    }


def test_create_purchase_order_generates_po_number_with_correct_format(db, sample_supplier, sample_warehouse, procurement_manager_user):
    purchase_order = create_purchase_order(
        {
            "supplier_id": sample_supplier.id,
            "warehouse_id": sample_warehouse.id,
            "items": [],
        },
        procurement_manager_user.id,
    )
    assert re.match(r"^PO-\d{8}-\d{4}$", purchase_order.po_number)


def test_approve_purchase_order_raises_exception_when_approver_is_same_as_creator(db, sample_supplier, sample_warehouse, procurement_manager_user):
    from apps.categories.models import Category
    from apps.products.models import Product

    category = Category.objects.create(category_code="CAT-POSELF", name="PO Self")
    product = Product.objects.create(
        sku="SKU-POSELF-00000001",
        name="PO Product",
        category=category,
        unit_price=10,
        unit_of_measure="pcs",
    )
    purchase_order = create_purchase_order(_purchase_order_data(sample_supplier, sample_warehouse, product), procurement_manager_user.id)
    submit_purchase_order(purchase_order.id)
    with pytest.raises(BusinessPermissionException):
        approve_purchase_order(purchase_order.id, procurement_manager_user.id)


def test_approve_purchase_order_raises_exception_when_status_is_not_pending_approval(db, sample_supplier, sample_warehouse, procurement_manager_user, warehouse_manager_user):
    purchase_order = create_purchase_order(
        {
            "supplier_id": sample_supplier.id,
            "warehouse_id": sample_warehouse.id,
            "items": [],
        },
        procurement_manager_user.id,
    )
    with pytest.raises(InvalidOperationException):
        approve_purchase_order(purchase_order.id, warehouse_manager_user.id)


def test_receive_purchase_order_updates_inventory_for_received_items(db, sample_supplier, sample_warehouse, sample_product, procurement_manager_user, warehouse_manager_user, staff_user):
    inventory = Inventory.objects.create(product=sample_product, warehouse=sample_warehouse, quantity_available=0)
    purchase_order = create_purchase_order(_purchase_order_data(sample_supplier, sample_warehouse, sample_product, quantity=5), procurement_manager_user.id)
    submit_purchase_order(purchase_order.id)
    approve_purchase_order(purchase_order.id, warehouse_manager_user.id)
    item = purchase_order.items.first()
    receive_purchase_order(
        purchase_order.id,
        {"items": [{"po_item_id": item.id, "quantity_received": 5}]},
        staff_user.id,
    )
    inventory.refresh_from_db()
    assert inventory.quantity_available == 5


def test_receive_purchase_order_sets_status_to_partially_received_when_not_all_items_received(db, sample_supplier, sample_warehouse, sample_product, procurement_manager_user, warehouse_manager_user):
    from apps.accounts.models import UserRole

    receiver = procurement_manager_user
    receiver.role = UserRole.STAFF
    receiver.save()
    Inventory.objects.create(product=sample_product, warehouse=sample_warehouse, quantity_available=0)
    purchase_order = create_purchase_order(_purchase_order_data(sample_supplier, sample_warehouse, sample_product, quantity=10), procurement_manager_user.id)
    submit_purchase_order(purchase_order.id)
    approve_purchase_order(purchase_order.id, warehouse_manager_user.id)
    item = purchase_order.items.first()
    receive_purchase_order(
        purchase_order.id,
        {"items": [{"po_item_id": item.id, "quantity_received": 4}]},
        receiver.id,
    )
    purchase_order.refresh_from_db()
    assert purchase_order.status == PurchaseOrderStatus.PARTIALLY_RECEIVED


def test_cancel_purchase_order_raises_exception_when_status_is_received(db, sample_supplier, sample_warehouse, procurement_manager_user, warehouse_manager_user):
    from apps.categories.models import Category
    from apps.products.models import Product

    category = Category.objects.create(category_code="CAT-POCANCEL", name="PO Cancel")
    product = Product.objects.create(
        sku="SKU-POCANCEL-00000001",
        name="PO Cancel Product",
        category=category,
        unit_price=10,
        unit_of_measure="pcs",
    )
    Inventory.objects.create(product=product, warehouse=sample_warehouse, quantity_available=0)
    purchase_order = create_purchase_order(_purchase_order_data(sample_supplier, sample_warehouse, product, quantity=3), procurement_manager_user.id)
    submit_purchase_order(purchase_order.id)
    approve_purchase_order(purchase_order.id, warehouse_manager_user.id)
    item = purchase_order.items.first()
    receive_purchase_order(
        purchase_order.id,
        {"items": [{"po_item_id": item.id, "quantity_received": 3}]},
        procurement_manager_user.id,
    )
    with pytest.raises(InvalidOperationException):
        cancel_purchase_order(purchase_order.id, "cannot cancel")
