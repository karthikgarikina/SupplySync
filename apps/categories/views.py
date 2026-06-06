from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories import services
from apps.categories.serializers import CategorySerializer, CategoryTreeSerializer
from core.pagination import StandardResultsPagination
from core.permissions import IsWarehouseManagerOrAdmin


class CategoryListCreateView(APIView):
    """List categories or create a category."""

    pagination_class = StandardResultsPagination
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsWarehouseManagerOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(services.list_categories(), request, view=self)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = services.create_category(serializer.validated_data)
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryTreeView(APIView):
    """Return the full recursive category hierarchy."""

    permission_classes = [IsAuthenticated]
    serializer_class = CategoryTreeSerializer

    def get(self, request):
        serializer = CategoryTreeSerializer(services.get_category_tree(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
