# SupplySync Backend

Production-grade inventory and order management backend built with Django, Django REST Framework, PostgreSQL, Redis, Celery, Celery Beat, Simple JWT, django-filter, drf-spectacular, and pytest.

## Requirements

- Python 3.11 or 3.12
- Docker Desktop
- Git

## Clone And Setup

```powershell
git clone https://github.com/karthikgarikina/SupplySync
cd SupplySync

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env
```

If you are on macOS/Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Start Infrastructure

```powershell
docker compose up -d postgres redis
```

This starts:

- PostgreSQL 15 on host port `5432`
- Redis 7 on host port `6379`

## Run The API: Normal Way

Use this if your local machine does not already have another PostgreSQL server using port `5432`.

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

The API will run at:

```text
http://127.0.0.1:8000/
```

## Run The API: Docker-Network Workaround

Use this if `python manage.py migrate` gives a password error like:

```text
password authentication failed for user "supplysync_user"
```

That usually means a local Windows PostgreSQL process is also listening on `5432`, so your host-side Django command is reaching the wrong database.

Run migrations and the API inside the Docker Compose network:

```powershell
docker compose up -d postgres redis
docker compose run --rm celery_worker python manage.py migrate --noinput
docker compose run --rm -p 8000:8000 celery_worker python manage.py runserver 0.0.0.0:8000
```

Then open:

```text
http://127.0.0.1:8000/
```

## Stop Services

```powershell
docker compose down
```

To remove the PostgreSQL volume and start with a fresh database:

```powershell
docker compose down -v
```

## Background Workers

Start Celery worker and Celery Beat:

```powershell
docker compose up celery_worker celery_beat
```

The worker runs:

```text
celery -A supplysync worker -l info
```

Celery Beat runs:

```text
celery -A supplysync beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## API Documentation UI

After the API server is running, open these URLs:

```text
Swagger UI:     http://127.0.0.1:8000/api/schema/swagger-ui/
ReDoc UI:       http://127.0.0.1:8000/api/schema/redoc/
OpenAPI Schema: http://127.0.0.1:8000/api/schema/
Django Admin:   http://127.0.0.1:8000/admin/
```

## Django Admin Access

The Django admin login does not use only the API role value. A user with `role: "ADMIN"` from `/api/v1/auth/register/` is an application admin role, but Django admin also requires:

- `is_staff=True`
- `is_superuser=True`

Create a Django admin account with the normal host-side command:

```powershell
python manage.py createsuperuser
```

Because this project uses email login, use the email address as the username on the admin login page:

```text
http://127.0.0.1:8000/admin/
```

If you are using the Docker-network workaround because local PostgreSQL conflicts with port `5432`, create the admin account inside Docker instead:

```powershell
docker compose run --rm celery_worker python manage.py createsuperuser
```

Example values:

```text
Email: garikinakarthik459@gmail.com
Username: admin
Full name: Admin User
Password: Password1!
```

Then login to Django admin with:

```text
Email: garikinakarthik459@gmail.com
Password: Password1!
```

## Video Demo
https://www.youtube.com/watch?v=TFij-SXhoJs

## Authentication

Register a user:

```http
POST /api/v1/auth/register/
```

Example body:

```json
{
  "username": "staff1",
  "email": "staff1@example.com",
  "password": "Password1!",
  "full_name": "Staff One",
  "role": "STAFF"
}
```

Login:

```http
POST /api/v1/auth/login/
```

Example body:

```json
{
  "email": "staff1@example.com",
  "password": "Password1!"
}
```

Use the returned access token on protected endpoints:

```text
Authorization: Bearer <access_token>
```

Useful roles:

- `ADMIN`
- `WAREHOUSE_MANAGER`
- `PROCUREMENT_MANAGER`
- `STAFF`

## Main API Endpoints

Auth:

```text
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/logout/
POST /api/v1/auth/change-password/
```

Warehouses:

```text
GET    /api/v1/warehouses/
POST   /api/v1/warehouses/
GET    /api/v1/warehouses/<id>/
PUT    /api/v1/warehouses/<id>/
DELETE /api/v1/warehouses/<id>/
```

Categories:

```text
GET  /api/v1/categories/
POST /api/v1/categories/
GET  /api/v1/categories/tree/
```

Products:

```text
GET  /api/v1/products/
POST /api/v1/products/
GET  /api/v1/products/<id>/
```

Product filters:

```text
/api/v1/products/?category_id=1
/api/v1/products/?is_active=true
/api/v1/products/?min_price=100&max_price=500
/api/v1/products/?search=scanner
```

Suppliers:

```text
GET    /api/v1/suppliers/
POST   /api/v1/suppliers/
GET    /api/v1/suppliers/<id>/
PUT    /api/v1/suppliers/<id>/
DELETE /api/v1/suppliers/<id>/
```

Inventory:

```text
POST /api/v1/inventory/adjust/
POST /api/v1/inventory/transfer/
GET  /api/v1/inventory/low-stock/
GET  /api/v1/inventory/warehouse/<warehouse_id>/
```

Purchase Orders:

```text
GET  /api/v1/purchase-orders/
POST /api/v1/purchase-orders/
POST /api/v1/purchase-orders/<id>/submit/
POST /api/v1/purchase-orders/<id>/approve/
POST /api/v1/purchase-orders/<id>/receive/
POST /api/v1/purchase-orders/<id>/cancel/
```

Sales Orders:

```text
GET  /api/v1/sales-orders/
POST /api/v1/sales-orders/
POST /api/v1/sales-orders/<id>/dispatch/
POST /api/v1/sales-orders/<id>/deliver/
POST /api/v1/sales-orders/<id>/cancel/
```

Reports:

```text
GET /api/v1/reports/dashboard/
GET /api/v1/reports/inventory-valuation/
GET /api/v1/reports/purchase-orders/summary/
GET /api/v1/reports/sales-orders/summary/
```

Report filters:

```text
/api/v1/reports/inventory-valuation/?warehouse_id=1
/api/v1/reports/purchase-orders/summary/?start_date=2026-06-01&end_date=2026-06-30
/api/v1/reports/purchase-orders/summary/?supplier_id=1&status=APPROVED
/api/v1/reports/sales-orders/summary/?warehouse_id=1&status=DELIVERED
```

## Suggested Manual Testing Order

1. Register one user for each role: `ADMIN`, `WAREHOUSE_MANAGER`, `PROCUREMENT_MANAGER`, `STAFF`.
2. Login and copy the access token.
3. Create a warehouse as `ADMIN`.
4. Create a category as `ADMIN` or `WAREHOUSE_MANAGER`.
5. Create a product as `ADMIN` or `WAREHOUSE_MANAGER`.
6. Create a supplier as `PROCUREMENT_MANAGER`.
7. Add inventory with `POST /api/v1/inventory/adjust/` using `INBOUND`.
8. Test low-stock with `GET /api/v1/inventory/low-stock/`.
9. Create a second warehouse and test `POST /api/v1/inventory/transfer/`.
10. Create, submit, approve, receive, and cancel purchase orders.
11. Create, dispatch, deliver, and cancel sales orders.
12. Check all report endpoints.

## Common Request Examples

Inventory inbound adjustment:

```json
{
  "product_id": 1,
  "warehouse_id": 1,
  "transaction_type": "INBOUND",
  "quantity": 100,
  "notes": "Initial stock"
}
```

Inventory transfer:

```json
{
  "product_id": 1,
  "source_warehouse_id": 1,
  "destination_warehouse_id": 2,
  "quantity": 10,
  "notes": "Branch transfer"
}
```

Purchase order create:

```json
{
  "supplier_id": 1,
  "warehouse_id": 1,
  "expected_delivery_date": "2026-06-30",
  "notes": "Monthly purchase",
  "items": [
    {
      "product_id": 1,
      "quantity_ordered": 50,
      "unit_price": "100.00"
    }
  ]
}
```

Purchase order receive:

```json
{
  "items": [
    {
      "po_item_id": 1,
      "quantity_received": 25
    }
  ],
  "actual_delivery_date": "2026-06-30"
}
```

Sales order create:

```json
{
  "customer_name": "Acme Client",
  "customer_email": "client@example.com",
  "customer_phone": "9999999999",
  "shipping_address": "Client address",
  "warehouse_id": 1,
  "notes": "Urgent delivery",
  "items": [
    {
      "product_id": 1,
      "quantity": 5,
      "unit_price": "100.00"
    }
  ]
}
```

## Troubleshooting

Check running containers:

```powershell
docker compose ps
```

Check PostgreSQL logs:

```powershell
docker compose logs postgres
```

Check if another process is using port `5432`:

```powershell
netstat -ano | findstr :5432
```

If a local Windows `postgres.exe` process is also listening on `5432`, either stop it from an Administrator PowerShell or use the Docker-network workaround above.

Stop a conflicting process from Administrator PowerShell:

```powershell
taskkill /PID <PID> /F
```

## Tests

Run tests with SQLite-based isolated settings:

```powershell
python -m pytest
```

Run Django checks:

```powershell
$env:DJANGO_SETTINGS_MODULE='supplysync.settings.testing'
python manage.py check
python manage.py makemigrations --check --dry-run
```
