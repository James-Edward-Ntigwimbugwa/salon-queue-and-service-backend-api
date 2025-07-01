from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from services.models import Service
from inventory.models import Product
import uuid

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('SERVICE', 'Service Booking'),
        ('PRODUCT', 'Product Purchase'),
        ('COMBO', 'Service + Product'),
    ]
    
    # Order identification
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='SERVICE')
    
    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Service-specific fields
    scheduled_date = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in minutes")
    assigned_staff = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_orders',
        limit_choices_to={'is_staff': True}
    )
    
    # Additional information
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    customer_rating = models.PositiveIntegerField(null=True, blank=True, help_text="Rating from 1-5")
    customer_feedback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        prefix = "ORD"
        timestamp = timezone.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}-{timestamp}-{random_part}"
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer.email}"
    
    def calculate_total(self):
        """Calculate total amount from order items"""
        service_total = sum(item.subtotal for item in self.service_items.all())
        product_total = sum(item.subtotal for item in self.product_items.all())
        self.total_amount = service_total + product_total
        self.final_amount = self.total_amount - self.discount_amount
        self.save()
        return self.final_amount
    
    def confirm_order(self, staff_user=None):
        """Confirm the order"""
        self.status = 'CONFIRMED'
        self.confirmed_at = timezone.now()
        if staff_user:
            self.assigned_staff = staff_user
        self.save()
    
    def start_service(self):
        """Mark order as in progress"""
        self.status = 'IN_PROGRESS'
        self.save()
    
    def complete_order(self):
        """Mark order as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        # Reduce stock for products used
        for item in self.product_items.all():
            item.product.reduce_stock(item.quantity)
        
        # Update service usage count
        for item in self.service_items.all():
            # Update product usage from services
            for service_product in item.service.service_products.all():
                service_product.product.reduce_stock(
                    service_product.quantity_used * item.quantity
                )
    
    def cancel_order(self, reason=""):
        """Cancel the order"""
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.notes = f"{self.notes}\nCancellation reason: {reason}" if reason else self.notes
        self.save()
    
    def add_rating(self, rating, feedback=""):
        """Add customer rating and feedback"""
        self.customer_rating = rating
        self.customer_feedback = feedback
        self.save()

class OrderServiceItem(models.Model):
    """Services included in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='service_items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Service execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.service.name} x{self.quantity}"
    
    def start_service(self):
        """Mark service as started"""
        self.started_at = timezone.now()
        self.save()
    
    def complete_service(self, notes=""):
        """Mark service as completed"""
        self.completed_at = timezone.now()
        self.staff_notes = notes
        self.save()

class OrderProductItem(models.Model):
    """Products included in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='product_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} x{self.quantity}"

class Cart(models.Model):
    """Shopping cart for users"""
    customer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.customer.email}"
    
    def get_total(self):
        """Calculate cart total"""
        service_total = sum(item.subtotal for item in self.service_items.all())
        product_total = sum(item.subtotal for item in self.product_items.all())
        return service_total + product_total
    
    def clear(self):
        """Clear all items from cart"""
        self.service_items.all().delete()
        self.product_items.all().delete()
    
    def convert_to_order(self):
        """Convert cart to order"""
        if not self.service_items.exists() and not self.product_items.exists():
            return None
        
        # Determine order type
        has_services = self.service_items.exists()
        has_products = self.product_items.exists()
        
        if has_services and has_products:
            order_type = 'COMBO'
        elif has_services:
            order_type = 'SERVICE'
        else:
            order_type = 'PRODUCT'
        
        # Create order
        order = Order.objects.create(
            customer=self.customer,
            order_type=order_type,
            total_amount=0,
            final_amount=0
        )
        
        # Transfer service items
        for cart_item in self.service_items.all():
            OrderServiceItem.objects.create(
                order=order,
                service=cart_item.service,
                quantity=cart_item.quantity,
                unit_price=cart_item.service.price,
                subtotal=cart_item.subtotal
            )
        
        # Transfer product items
        for cart_item in self.product_items.all():
            OrderProductItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                subtotal=cart_item.subtotal
            )
        
        # Calculate totals
        order.calculate_total()
        
        # Clear cart
        self.clear()
        
        return order

class CartServiceItem(models.Model):
    """Service items in cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='service_items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'service')
    
    @property
    def subtotal(self):
        return self.quantity * self.service.price
    
    def __str__(self):
        return f"{self.cart.customer.email} - {self.service.name} x{self.quantity}"

class CartProductItem(models.Model):
    """Product items in cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='product_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    @property
    def subtotal(self):
        return self.quantity * self.product.price
    
    def __str__(self):
        return f"{self.cart.customer.email} - {self.product.name} x{self.quantity}"

class OrderStatusHistory(models.Model):
    """Track order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"