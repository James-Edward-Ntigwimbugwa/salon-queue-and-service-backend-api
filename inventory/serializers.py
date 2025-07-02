from rest_framework import serializers
from .models import ProductCategory, Product

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'image', 'is_active', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'category_name', 'sku', 'price',
            'cost_price', 'stock_quantity', 'min_stock_level', 'max_stock_level',
            'unit', 'image', 'is_active', 'is_sellable', 'usage_count', 'created_at', 'updated_at'
        ]
