from rest_framework import generics, permissions
from .models import ProductCategory, Product
from .serializers import ProductCategorySerializer, ProductSerializer

class ProductCategoryListView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
