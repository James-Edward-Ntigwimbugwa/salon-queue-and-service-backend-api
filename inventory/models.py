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
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='service_products')
    quantity_used = models.PositiveIntegerField(default=1, help_text="Quantity of product used in the service")
    
    class Meta:
        unique_together = ('service', 'product')
    
    def __str__(self):
        return f"{self.service.name} - {self.product.name} ({self.quantity_used})"

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('SERVICE_USE', 'Used in Service'),
        ('SALE', 'Product Sale'),
        ('WASTE', 'Waste/Damage'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Can be negative for OUT movements
    reference_id = models.CharField(max_length=100, null=True, blank=True, help_text="Reference to order, service, etc.")
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('CONFIRMED', 'Confirmed'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"PO-{self.order_number}"
    
    def calculate_total(self):
        total = sum(item.total_cost for item in self.items.all())
        self.total_amount = total
        self.save()
        return total

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total_cost(self):
        return self.quantity_ordered * self.unit_cost
    
    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.product.name}"