from django.urls import path

from apps.sales_orders.views import SalesOrderCancelView, SalesOrderDeliverView, SalesOrderDispatchView, SalesOrderListCreateView

urlpatterns = [
    path("", SalesOrderListCreateView.as_view(), name="sales-order-list-create"),
    path("<int:pk>/dispatch/", SalesOrderDispatchView.as_view(), name="sales-order-dispatch"),
    path("<int:pk>/deliver/", SalesOrderDeliverView.as_view(), name="sales-order-deliver"),
    path("<int:pk>/cancel/", SalesOrderCancelView.as_view(), name="sales-order-cancel"),
]

