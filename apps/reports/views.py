from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports import services
from apps.reports.serializers import (
    DashboardReportSerializer,
    InventoryValuationReportSerializer,
    PurchaseOrderSummaryReportSerializer,
    SalesOrderSummaryReportSerializer,
)
from core.permissions import IsProcurementManagerOrAdmin, IsWarehouseManagerOrAdmin


class DashboardReportView(APIView):
    """Return dashboard analytics."""

    permission_classes = [IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]
    serializer_class = DashboardReportSerializer

    def get(self, request):
        return Response(DashboardReportSerializer(services.get_dashboard_summary()).data, status=status.HTTP_200_OK)


class InventoryValuationReportView(APIView):
    """Return inventory valuation by warehouse."""

    permission_classes = [IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]
    serializer_class = InventoryValuationReportSerializer

    def get(self, request):
        warehouse_id = request.query_params.get("warehouse_id")
        report = services.get_inventory_valuation(int(warehouse_id) if warehouse_id else None)
        return Response(InventoryValuationReportSerializer(report).data, status=status.HTTP_200_OK)


class PurchaseOrderSummaryReportView(APIView):
    """Return purchase order summary metrics."""

    permission_classes = [IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]
    serializer_class = PurchaseOrderSummaryReportSerializer

    def get(self, request):
        report = services.get_purchase_order_summary(
            request.query_params.get("start_date"),
            request.query_params.get("end_date"),
            request.query_params.get("supplier_id"),
            request.query_params.get("status"),
        )
        return Response(PurchaseOrderSummaryReportSerializer(report).data, status=status.HTTP_200_OK)


class SalesOrderSummaryReportView(APIView):
    """Return sales order summary metrics."""

    permission_classes = [IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]
    serializer_class = SalesOrderSummaryReportSerializer

    def get(self, request):
        report = services.get_sales_order_summary(
            request.query_params.get("start_date"),
            request.query_params.get("end_date"),
            request.query_params.get("warehouse_id"),
            request.query_params.get("status"),
        )
        return Response(SalesOrderSummaryReportSerializer(report).data, status=status.HTTP_200_OK)
