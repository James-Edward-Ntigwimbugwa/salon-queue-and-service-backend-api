from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='service_categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Service Categories"
    
    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    image = models.ImageField(upload_to='services/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    requires_appointment = models.BooleanField(default=True)
    loyalty_points = models.PositiveIntegerField(default=0, help_text="Points earned for this service")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        ratings = self.feedback_set.all()
        if ratings:
            return sum(rating.rating for rating in ratings) / len(ratings)
        return 0
    
    @property
    def total_reviews(self):
        return self.feedback_set.count()

class ServiceStaff(models.Model):
    """Assign staff members to specific services"""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'staff'})
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['staff', 'service']
    
    def __str__(self):
        return f"{self.staff.username} - {self.service.name}"

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'customer'})
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['customer', 'service']
    
    def __str__(self):
        return f"{self.customer.username} - {self.service.name} ({self.rating}/5)"