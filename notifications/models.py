from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class NotificationType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    CHANNEL_CHOICES = [
        ('PUSH', 'Push Notification'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('IN_APP', 'In-App'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('READ', 'Read'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='PUSH')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Optional data for specific notifications
    data = models.JSONField(default=dict, blank=True, help_text="Additional data for the notification")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional expiry
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        if self.status != 'READ':
            self.status = 'READ'
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_sent(self):
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_delivered(self):
        self.status = 'DELIVERED'
        self.save()
    
    def mark_as_failed(self):
        self.status = 'FAILED'
        self.save()

class NotificationTemplate(models.Model):
    """Templates for common notifications"""
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    title_template = models.CharField(max_length=200, help_text="Use {variable} for dynamic content")
    message_template = models.TextField(help_text="Use {variable} for dynamic content")
    default_channel = models.CharField(max_length=20, choices=Notification.CHANNEL_CHOICES, default='PUSH')
    default_priority = models.CharField(max_length=20, choices=Notification.PRIORITY_CHOICES, default='MEDIUM')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def render(self, context):
        """Render template with given context"""
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        return title, message

class UserNotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Notification type preferences
    queue_updates = models.BooleanField(default=True)
    booking_confirmations = models.BooleanField(default=True)
    payment_confirmations = models.BooleanField(default=True)
    promotions = models.BooleanField(default=True)
    service_reminders = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(null=True, blank=True, help_text="Start of quiet hours (no notifications)")
    quiet_hours_end = models.TimeField(null=True, blank=True, help_text="End of quiet hours")
    
    def __str__(self):
        return f"{self.user.email} preferences"

class NotificationLog(models.Model):
    """Log of all notification attempts"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    attempt_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    error_message = models.TextField(blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-attempt_at']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.notification.title} - {status}"