from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory import services
from apps.inventory.serializers import (
    InventoryAdjustSerializer,
    InventorySnapshotSerializer,
    InventoryTransactionSerializer,
    InventoryTransferSerializer,
    LowStockAlertSerializer,
)
from core.pagination import StandardResultsPagination
from core.permissions import IsWarehouseManagerOrAdmin, IsWarehouseManagerOrAdminOrStaff


class InventoryAdjustView(APIView):
    """Adjust inventory for a product at a warehouse."""

    permission_classes = [IsWarehouseManagerOrAdminOrStaff]

    @extend_schema(request=InventoryAdjustSerializer, responses=InventoryTransactionSerializer)
    def post(self, request):
        serializer = InventoryAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory_transaction = services.adjust_inventory(serializer.validated_data, request.user.id)
        return Response(InventoryTransactionSerializer(inventory_transaction).data, status=status.HTTP_200_OK)


class InventoryTransferView(APIView):
    """Transfer inventory between two warehouses."""

    permission_classes = [IsWarehouseManagerOrAdmin]

    @extend_schema(request=InventoryTransferSerializer)
    def post(self, request):
        serializer = InventoryTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.transfer_inventory(serializer.validated_data, request.user.id)
        return Response(
            {
                "reference_id": result["reference_id"],
                "source_transaction": InventoryTransactionSerializer(result["source_transaction"]).data,
                "destination_transaction": InventoryTransactionSerializer(result["destination_transaction"]).data,
            },
            status=status.HTTP_200_OK,
        )


class LowStockAlertView(APIView):
    """Return cached low-stock alerts."""

    permission_classes = [IsWarehouseManagerOrAdmin]

    def get(self, request):
        serializer = LowStockAlertSerializer(services.get_low_stock_alerts(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WarehouseInventoryView(APIView):
    """Return a paginated inventory snapshot for a warehouse."""

    permission_classes = [IsWarehouseManagerOrAdminOrStaff]
    pagination_class = StandardResultsPagination

    def get(self, request, warehouse_id):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(services.get_warehouse_inventory(warehouse_id), request, view=self)
        serializer = InventorySnapshotSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

