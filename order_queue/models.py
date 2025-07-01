# queue/models.py
from django.db import models
from django.contrib.auth import get_user_model
from services.models import Service
import uuid
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class QueueManager(models.Manager):
    def get_active_queue(self):
        """Get all active queue items ordered by join time"""
        return self.filter(status='waiting').order_by('time_joined')
    
    def get_customer_position(self, customer):
        """Get customer's position in queue"""
        active_queue = self.get_active_queue()
        try:
            customer_queue = active_queue.get(customer=customer)
            position = list(active_queue).index(customer_queue) + 1
            return position
        except self.model.DoesNotExist:
            return None
    
    def estimate_wait_time(self, customer):
        """Estimate wait time for a customer based on queue position and service durations"""
        position = self.get_customer_position(customer)
        if not position:
            return 0
        
        # Get all customers ahead in queue
        customers_ahead = self.get_active_queue()[:position-1]
        total_duration = 0
        
        for queue_item in customers_ahead:
            # Sum up durations of all services in the booking
            for service in queue_item.booking.services.all():
                total_duration += service.duration
        
        return total_duration

class Queue(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'customer'})
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='queue_item')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    time_joined = models.DateTimeField(auto_now_add=True)
    time_started = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    estimated_start_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    staff_assigned = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'role': 'staff'},
        related_name='assigned_queue_items'
    )
    
    objects = QueueManager()
    
    class Meta:
        ordering = ['time_joined']
    
    def __str__(self):
        return f"Queue #{self.id} - {self.customer.username} ({self.status})"
    
    @property
    def position_in_queue(self):
        return Queue.objects.get_customer_position(self.customer)
    
    @property
    def estimated_wait_time(self):
        return Queue.objects.estimate_wait_time(self.customer)
    
    @property
    def total_service_duration(self):
        return sum(service.duration for service in self.booking.services.all())
    
    def start_service(self, staff_member=None):
        """Mark service as started"""
        self.status = 'in_progress'
        self.time_started = timezone.now()
        if staff_member:
            self.staff_assigned = staff_member
        self.save()
    
    def complete_service(self):
        """Mark service as completed"""
        self.status = 'completed'
        self.time_completed = timezone.now()
        self.save()
    
    def cancel_service(self):
        """Cancel the service"""
        self.status = 'cancelled'
        self.save()

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'customer'})
    services = models.ManyToManyField(Service, through='BookingService')
    booking_date = models.DateTimeField(auto_now_add=True)
    preferred_date = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_duration = models.PositiveIntegerField(default=0, help_text="Total duration in minutes")
    special_requests = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.customer.username}"
    
    def calculate_totals(self):
        """Calculate total amount and duration"""
        booking_services = self.bookingservice_set.all()
        self.total_amount = sum(bs.service.price * bs.quantity for bs in booking_services)
        self.total_duration = sum(bs.service.duration * bs.quantity for bs in booking_services)
        self.save()
    
    def confirm_booking(self):
        """Confirm booking and add to queue"""
        self.is_confirmed = True
        self.save()
        
        # Create queue item
        queue_item = Queue.objects.create(
            customer=self.customer,
            booking=self,
            estimated_start_time=timezone.now() + timedelta(minutes=self.get_estimated_wait_time())
        )
        return queue_item
    
    def get_estimated_wait_time(self):
        """Get estimated wait time for this booking"""
        active_queue = Queue.objects.get_active_queue()
        total_wait = sum(queue_item.total_service_duration for queue_item in active_queue)
        return total_wait

class BookingService(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['booking', 'service']
    
    def __str__(self):
        return f"{self.booking.id} - {self.service.name} (x{self.quantity})"
    
    @property
    def subtotal(self):
        return self.service.price * self.quantity
    
    @property
    def total_duration(self):
        return self.service.duration * self.quantity