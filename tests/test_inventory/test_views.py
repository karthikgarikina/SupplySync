from rest_framework import status

from apps.warehouses.models import Warehouse


def test_adjust_inventory_returns_200_for_authorized_user(authenticated_staff_client, sample_inventory):
    response = authenticated_staff_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": sample_inventory.product_id,
            "warehouse_id": sample_inventory.warehouse_id,
            "transaction_type": "INBOUND",
            "quantity": 1,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_adjust_inventory_returns_403_for_unauthorized_role(authenticated_pm_client, sample_inventory):
    response = authenticated_pm_client.post(
        "/api/v1/inventory/adjust/",
        {
            "product_id": sample_inventory.product_id,
            "warehouse_id": sample_inventory.warehouse_id,
            "transaction_type": "INBOUND",
            "quantity": 1,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_low_stock_alerts_returns_200_with_list(authenticated_wm_client, sample_inventory):
    sample_inventory.quantity_available = 1
    sample_inventory.save()
    response = authenticated_wm_client.get("/api/v1/inventory/low-stock/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)


def test_transfer_inventory_returns_200_with_valid_request(authenticated_wm_client, sample_inventory, sample_warehouse):
    destination = Warehouse.objects.create(
        warehouse_code="WH-VIEW01",
        name="View Destination",
        location="View Road",
        city="Mangaluru",
        state="Karnataka",
        pincode="575001",
        capacity=3000,
    )
    response = authenticated_wm_client.post(
        "/api/v1/inventory/transfer/",
        {
            "product_id": sample_inventory.product_id,
            "source_warehouse_id": sample_inventory.warehouse_id,
            "destination_warehouse_id": destination.id,
            "quantity": 2,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

