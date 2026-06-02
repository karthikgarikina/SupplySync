from decimal import Decimal

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, UserRole
from apps.categories.models import Category
from apps.inventory.models import Inventory
from apps.products.models import Product
from apps.suppliers.models import Supplier
from apps.warehouses.models import Warehouse


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@supplysync.local",
        password="Password1!",
        username="admin",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def warehouse_manager_user(db):
    return User.objects.create_user(
        email="wm@supplysync.local",
        password="Password1!",
        username="wm",
        full_name="Warehouse Manager",
        role=UserRole.WAREHOUSE_MANAGER,
    )


@pytest.fixture
def procurement_manager_user(db):
    return User.objects.create_user(
        email="pm@supplysync.local",
        password="Password1!",
        username="pm",
        full_name="Procurement Manager",
        role=UserRole.PROCUREMENT_MANAGER,
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email="staff@supplysync.local",
        password="Password1!",
        username="staff",
        full_name="Staff User",
        role=UserRole.STAFF,
    )


def _authenticated_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    return _authenticated_client(api_client, admin_user)


@pytest.fixture
def authenticated_wm_client(api_client, warehouse_manager_user):
    return _authenticated_client(api_client, warehouse_manager_user)


@pytest.fixture
def authenticated_pm_client(api_client, procurement_manager_user):
    return _authenticated_client(api_client, procurement_manager_user)


@pytest.fixture
def authenticated_staff_client(api_client, staff_user):
    return _authenticated_client(api_client, staff_user)


@pytest.fixture
def sample_warehouse(db):
    return Warehouse.objects.create(
        warehouse_code="WH-SAMPLE1",
        name="Primary Warehouse",
        location="Main Road",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        capacity=10000,
    )


@pytest.fixture
def sample_category(db):
    return Category.objects.create(category_code="CAT-SAMPLE", name="Electronics")


@pytest.fixture
def sample_product(db, sample_category):
    return Product.objects.create(
        sku="SKU-CAT-SAMPLE-TEST0001",
        name="Barcode Scanner",
        description="Handheld scanner",
        category=sample_category,
        unit_price=Decimal("100.00"),
        unit_of_measure="pcs",
        reorder_level=10,
    )


@pytest.fixture
def sample_supplier(db):
    return Supplier.objects.create(
        supplier_code="SUP-SAMPLE",
        name="Supply Vendor",
        contact_person="Vendor Contact",
        email="vendor@supplysync.local",
        phone="9999999999",
        address="Vendor Street",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
    )


@pytest.fixture
def sample_inventory(db, sample_product, sample_warehouse):
    return Inventory.objects.create(
        product=sample_product,
        warehouse=sample_warehouse,
        quantity_available=100,
        quantity_reserved=0,
        quantity_damaged=0,
    )

