from django.urls import path

from apps.products.views import ProductDetailView, ProductListCreateView

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="product-list-create"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
]

