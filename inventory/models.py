from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from services.models import Service

User = get_user_model()

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='product_categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=5, help_text="Minimum stock level for alerts")
    max_stock_level = models.PositiveIntegerField(default=100)
    unit = models.CharField(max_length=20, default='piece', help_text="Unit of measurement (piece, ml, g, etc.)")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_sellable = models.BooleanField(default=True, help_text="Can customers purchase this product?")
    usage_count = models.PositiveIntegerField(default=0, help_text="How many times used in services")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def stock_value(self):
        return self.stock_quantity * self.cost_price
    
    def reduce_stock(self, quantity):
        """Reduce stock quantity"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.usage_count += quantity
            self.save()
            return True
        return False
    
    def add_stock(self, quantity):
        """Add stock quantity"""
        self.stock_quantity += quantity
        self.save()

class ServiceProduct(models.Model):
    """Link products to services (products used in services)"""
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_used = models.PositiveIntegerField(default=1, help_text="Quantity of product used in the service")