from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.warehouses import services
from apps.warehouses.serializers import WarehouseDetailSerializer, WarehouseSerializer
from core.pagination import StandardResultsPagination
from core.permissions import IsAdminUser


class WarehouseListCreateView(APIView):
    """List active warehouses or create a warehouse."""

    pagination_class = StandardResultsPagination
    serializer_class = WarehouseSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @extend_schema(operation_id="warehouse_list")
    def get(self, request):
        queryset = services.list_warehouses(request.query_params.dict())
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = WarehouseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = WarehouseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = services.create_warehouse(serializer.validated_data)
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_201_CREATED)


class WarehouseDetailView(APIView):
    """Retrieve, update, or soft delete a warehouse."""

    serializer_class = WarehouseDetailSerializer

    def get_permissions(self):
        if self.request.method in {"PUT", "DELETE"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @extend_schema(operation_id="warehouse_retrieve")
    def get(self, request, pk):
        result = services.get_warehouse_with_summary(pk)
        return Response(WarehouseDetailSerializer(result).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        serializer = WarehouseSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        warehouse = services.update_warehouse(pk, serializer.validated_data)
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        services.delete_warehouse(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
