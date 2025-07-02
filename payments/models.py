from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('MOBILE', 'Mobile Payment'),
        ('OTHER', 'Other'),
    ]
    
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.order_number} - {self.status}"

class Transaction(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Transaction {self.id} for Payment {self.payment.id}"
