from django.urls import path

from apps.warehouses.views import WarehouseDetailView, WarehouseListCreateView

urlpatterns = [
    path("", WarehouseListCreateView.as_view(), name="warehouse-list-create"),
    path("<int:pk>/", WarehouseDetailView.as_view(), name="warehouse-detail"),
]

