from django.urls import path

from apps.purchase_orders.views import (
    PurchaseOrderApproveView,
    PurchaseOrderCancelView,
    PurchaseOrderListCreateView,
    PurchaseOrderReceiveView,
    PurchaseOrderSubmitView,
)

urlpatterns = [
    path("", PurchaseOrderListCreateView.as_view(), name="purchase-order-list-create"),
    path("<int:pk>/submit/", PurchaseOrderSubmitView.as_view(), name="purchase-order-submit"),
    path("<int:pk>/approve/", PurchaseOrderApproveView.as_view(), name="purchase-order-approve"),
    path("<int:pk>/receive/", PurchaseOrderReceiveView.as_view(), name="purchase-order-receive"),
    path("<int:pk>/cancel/", PurchaseOrderCancelView.as_view(), name="purchase-order-cancel"),
]

