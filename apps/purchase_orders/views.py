from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.purchase_orders import services
from apps.purchase_orders.serializers import PurchaseOrderCancelSerializer, PurchaseOrderOutputSerializer, PurchaseOrderReceiveSerializer, PurchaseOrderSerializer
from core.pagination import StandardResultsPagination
from core.permissions import IsProcurementManagerOrAdmin, IsWarehouseManagerOrAdmin, IsWarehouseManagerOrAdminOrStaff


class PurchaseOrderListCreateView(APIView):
    """List purchase orders or create a draft purchase order."""

    pagination_class = StandardResultsPagination
    serializer_class = PurchaseOrderSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsProcurementManagerOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(services.list_purchase_orders(), request, view=self)
        serializer = PurchaseOrderOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PurchaseOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_order = services.create_purchase_order(serializer.validated_data, request.user.id)
        return Response(PurchaseOrderOutputSerializer(purchase_order).data, status=status.HTTP_201_CREATED)


class PurchaseOrderSubmitView(APIView):
    """Submit a draft purchase order for approval."""

    permission_classes = [IsProcurementManagerOrAdmin]
    serializer_class = PurchaseOrderOutputSerializer

    @extend_schema(request=None, responses=PurchaseOrderOutputSerializer)
    def post(self, request, pk):
        return Response(PurchaseOrderOutputSerializer(services.submit_purchase_order(pk)).data, status=status.HTTP_200_OK)


class PurchaseOrderApproveView(APIView):
    """Approve a pending purchase order."""

    permission_classes = [IsWarehouseManagerOrAdmin]
    serializer_class = PurchaseOrderOutputSerializer

    @extend_schema(request=None, responses=PurchaseOrderOutputSerializer)
    def post(self, request, pk):
        purchase_order = services.approve_purchase_order(pk, request.user.id)
        return Response(PurchaseOrderOutputSerializer(purchase_order).data, status=status.HTTP_200_OK)


class PurchaseOrderReceiveView(APIView):
    """Receive goods for a purchase order."""

    permission_classes = [IsWarehouseManagerOrAdminOrStaff]
    serializer_class = PurchaseOrderReceiveSerializer

    @extend_schema(request=PurchaseOrderReceiveSerializer, responses=PurchaseOrderOutputSerializer)
    def post(self, request, pk):
        serializer = PurchaseOrderReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_order = services.receive_purchase_order(pk, serializer.validated_data, request.user.id)
        return Response(PurchaseOrderOutputSerializer(purchase_order).data, status=status.HTTP_200_OK)


class PurchaseOrderCancelView(APIView):
    """Cancel a purchase order when permitted."""

    permission_classes = [IsProcurementManagerOrAdmin]
    serializer_class = PurchaseOrderCancelSerializer

    @extend_schema(request=PurchaseOrderCancelSerializer, responses=PurchaseOrderOutputSerializer)
    def post(self, request, pk):
        serializer = PurchaseOrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_order = services.cancel_purchase_order(pk, serializer.validated_data.get("reason"))
        return Response(PurchaseOrderOutputSerializer(purchase_order).data, status=status.HTTP_200_OK)
