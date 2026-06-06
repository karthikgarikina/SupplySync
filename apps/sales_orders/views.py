from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sales_orders import services
from apps.sales_orders.serializers import SalesOrderCancelSerializer, SalesOrderOutputSerializer, SalesOrderSerializer
from core.pagination import StandardResultsPagination
from core.permissions import IsWarehouseManagerOrAdmin, IsWarehouseManagerOrAdminOrStaff


class SalesOrderListCreateView(APIView):
    """List sales orders or create a confirmed sales order."""

    pagination_class = StandardResultsPagination
    serializer_class = SalesOrderSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsWarehouseManagerOrAdminOrStaff()]
        return [IsAuthenticated()]

    def get(self, request):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(services.list_sales_orders(), request, view=self)
        serializer = SalesOrderOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SalesOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sales_order = services.create_sales_order(serializer.validated_data, request.user.id)
        return Response(SalesOrderOutputSerializer(sales_order).data, status=status.HTTP_201_CREATED)


class SalesOrderDispatchView(APIView):
    """Dispatch a sales order."""

    permission_classes = [IsWarehouseManagerOrAdmin]
    serializer_class = SalesOrderOutputSerializer

    @extend_schema(request=None, responses=SalesOrderOutputSerializer)
    def post(self, request, pk):
        return Response(SalesOrderOutputSerializer(services.dispatch_sales_order(pk)).data, status=status.HTTP_200_OK)


class SalesOrderDeliverView(APIView):
    """Mark a dispatched sales order as delivered."""

    permission_classes = [IsWarehouseManagerOrAdmin]
    serializer_class = SalesOrderOutputSerializer

    @extend_schema(request=None, responses=SalesOrderOutputSerializer)
    def post(self, request, pk):
        return Response(SalesOrderOutputSerializer(services.deliver_sales_order(pk)).data, status=status.HTTP_200_OK)


class SalesOrderCancelView(APIView):
    """Cancel a sales order and release inventory reservations."""

    permission_classes = [IsWarehouseManagerOrAdminOrStaff]
    serializer_class = SalesOrderCancelSerializer

    @extend_schema(request=SalesOrderCancelSerializer, responses=SalesOrderOutputSerializer)
    def post(self, request, pk):
        serializer = SalesOrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sales_order = services.cancel_sales_order(pk, serializer.validated_data.get("reason"))
        return Response(SalesOrderOutputSerializer(sales_order).data, status=status.HTTP_200_OK)
