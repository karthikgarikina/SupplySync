from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.products import services
from apps.products.filters import ProductFilter
from apps.products.models import Product
from apps.products.serializers import ProductDetailSerializer, ProductSerializer
from core.permissions import IsWarehouseManagerOrAdmin


class ProductListCreateView(GenericAPIView):
    """List filtered products or create a product."""

    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    queryset = Product.objects.all().order_by("id")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsWarehouseManagerOrAdmin()]
        return [IsAuthenticated()]

    @extend_schema(operation_id="product_list")
    def get(self, request):
        queryset = services.list_products(self.filter_queryset(self.get_queryset()))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = services.create_product(serializer.validated_data)
        return Response(self.get_serializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(GenericAPIView):
    """Return product detail with inventory by warehouse."""

    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer

    @extend_schema(operation_id="product_retrieve")
    def get(self, request, pk):
        return Response(self.get_serializer(services.get_product_with_inventory(pk)).data, status=status.HTTP_200_OK)
