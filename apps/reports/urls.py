from django.urls import path

from apps.reports.views import (
    DashboardReportView,
    InventoryValuationReportView,
    PurchaseOrderSummaryReportView,
    SalesOrderSummaryReportView,
)

urlpatterns = [
    path("dashboard/", DashboardReportView.as_view(), name="dashboard-report"),
    path("inventory-valuation/", InventoryValuationReportView.as_view(), name="inventory-valuation-report"),
    path("purchase-orders/summary/", PurchaseOrderSummaryReportView.as_view(), name="purchase-order-summary-report"),
    path("sales-orders/summary/", SalesOrderSummaryReportView.as_view(), name="sales-order-summary-report"),
]

