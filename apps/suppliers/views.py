from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.suppliers import services
from apps.suppliers.serializers import SupplierSerializer
from core.pagination import StandardResultsPagination
from core.permissions import IsProcurementManagerOrAdmin


class SupplierListCreateView(APIView):
    """List suppliers or create a supplier."""

    pagination_class = StandardResultsPagination
    serializer_class = SupplierSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsProcurementManagerOrAdmin()]
        return [IsAuthenticated()]

    @extend_schema(operation_id="supplier_list")
    def get(self, request):
        queryset = services.list_suppliers(request.query_params.dict(), 1, self.pagination_class.page_size)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SupplierSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = services.create_supplier(serializer.validated_data)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    """Retrieve, update, or soft delete a supplier."""

    permission_classes = [IsProcurementManagerOrAdmin]
    serializer_class = SupplierSerializer

    @extend_schema(operation_id="supplier_retrieve")
    def get(self, request, pk):
        return Response(SupplierSerializer(services.get_supplier_by_id(pk)).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        serializer = SupplierSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = services.update_supplier(pk, serializer.validated_data)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        services.delete_supplier(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
