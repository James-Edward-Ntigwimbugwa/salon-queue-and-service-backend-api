import logging
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification, NotificationLog, UserNotificationPreference

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationService:
    """Service class for handling notification sending"""
    
    def send_notification(self, notification):
        """Send a notification based on its channel"""
        try:
            # Check user preferences
            if not self._should_send_notification(notification):
                notification.status = 'CANCELLED'
                notification.save()
                return False
            
            success = False
            error_message = ""
            
            if notification.channel == 'EMAIL':
                success, error_message = self._send_email(notification)
            elif notification.channel == 'SMS':
                success, error_message = self._send_sms(notification)
            elif notification.channel == 'PUSH':
                success, error_message = self._send_push_notification(notification)
            elif notification.channel == 'IN_APP':
                success = True  # In-app notifications are already in the database
            
            # Update notification status
            if success:
                notification.mark_as_sent()
            else:
                notification.mark_as_failed()
            
            # Log the attempt
            NotificationLog.objects.create(
                notification=notification,
                success=success,
                error_message=error_message
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {str(e)}")
            notification.mark_as_failed()
            NotificationLog.objects.create(
                notification=notification,
                success=False,
                error_message=str(e)
            )
            return False
    
    def _should_send_notification(self, notification):
        """Check if notification should be sent based on user preferences"""
        try:
            preferences = notification.user.notification_preferences
            
            # Check channel preferences
            if notification.channel == 'EMAIL' and not preferences.email_notifications:
                return False
            if notification.channel == 'SMS' and not preferences.sms_notifications:
                return False
            if notification.channel == 'PUSH' and not preferences.push_notifications:
                return False
            
            # Check notification type preferences
            notification_type = notification.notification_type.name.lower()
            if 'queue' in notification_type and not preferences.queue_updates:
                return False
            if 'booking' in notification_type and not preferences.booking_confirmations:
                return False
            if 'payment' in notification_type and not preferences.payment_confirmations:
                return False
            if 'promotion' in notification_type and not preferences.promotions:
                return False
            if 'reminder' in notification_type and not preferences.service_reminders:
                return False
            
            # Check quiet hours
            if preferences.quiet_hours_start and preferences.quiet_hours_end:
                current_time = timezone.now().time()
                if preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end:
                    return False
            
            return True
            
        except UserNotificationPreference.DoesNotExist:
            # If no preferences set, allow all notifications
            return True
    
    def _send_email(self, notification):
        """Send email notification"""
        try:
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False
            )
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _send_sms(self, notification):
        """Send SMS notification"""
        try:
            # Here you would integrate with your SMS provider (e.g., Twilio, Africa's Talking)
            # For now, we'll just log it
            logger.info(f"SMS would be sent to {notification.user.phone}: {notification.message}")
            
            # Example integration with Africa's Talking (popular in Tanzania)
            # import africastalking
            # africastalking.initialize(username, api_key)
            # sms = africastalking.SMS
            # response = sms.send(notification.message, [notification.user.phone])
            
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _send_push_notification(self, notification):
        """Send push notification"""
        try:
            # Here you would integrate with Firebase Cloud Messaging or similar
            # For now, we'll just log it
            logger.info(f"Push notification would be sent: {notification.title}")
            
            # Example Firebase integration
            # from firebase_admin import messaging
            # message = messaging.Message(
            #     notification=messaging.Notification(
            #         title=notification.title,
            #         body=notification.message
            #     ),
            #     token=notification.user.fcm_token,
            #     data=notification.data
            # )
            # response = messaging.send(message)
            
            return True, ""
        except Exception as e:
            return False, str(e)

class NotificationTemplateService:
    """Service for creating notifications from templates"""
    
    @staticmethod
    def create_queue_notification(user, queue_position, estimated_wait_time):
        """Create queue position notification"""
        from .models import NotificationType, Notification
        
        notification_type, _ = NotificationType.objects.get_or_create(
            name='queue_update',
            defaults={'description': 'Queue position updates'}
        )
        
        title = "Queue Update"
        message = f"You are now #{queue_position} in the queue. Estimated wait time: {estimated_wait_time} minutes."
        
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            channel='PUSH',
            priority='MEDIUM',
            data={
                'queue_position': queue_position,
                'estimated_wait_time': estimated_wait_time
            }
        )
    
    @staticmethod
    def create_booking_confirmation(user, service_name, booking_time):
        """Create booking confirmation notification"""
        from .models import NotificationType, Notification
        
        notification_type, _ = NotificationType.objects.get_or_create(
            name='booking_confirmation',
            defaults={'description': 'Booking confirmations'}
        )
        
        title = "Booking Confirmed"
        message = f"Your {service_name} appointment has been confirmed for {booking_time}."
        
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            channel='EMAIL',
            priority='HIGH',
            data={
                'service_name': service_name,
                'booking_time': str(booking_time)
            }
        )
    
    @staticmethod
    def create_payment_confirmation(user, amount, payment_method):
        """Create payment confirmation notification"""
        from .models import NotificationType, Notification
        
        notification_type, _ = NotificationType.objects.get_or_create(
            name='payment_confirmation',
            defaults={'description': 'Payment confirmations'}
        )
        
        title = "Payment Received"
        message = f"Payment of TSh {amount:,.2f} received via {payment_method}. Thank you!"
        
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            channel='SMS',
            priority='HIGH',
            data={
                'amount': str(amount),
                'payment_method': payment_method
            }
        )
    
    @staticmethod
    def create_service_reminder(user, service_name, appointment_time):
        """Create service reminder notification"""
        from .models import NotificationType, Notification
        
        notification_type, _ = NotificationType.objects.get_or_create(
            name='service_reminder',
            defaults={'description': 'Service reminders'}
        )
        
        title = "Appointment Reminder"
        message = f"Reminder: Your {service_name} appointment is in 30 minutes at {appointment_time}."
        
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            channel='PUSH',
            priority='HIGH',
            data={
                'service_name': service_name,
                'appointment_time': str(appointment_time)
            }
        )
    
    @staticmethod
    def create_low_stock_alert(staff_users, product_name, current_stock):
        """Create low stock alert for staff"""
        from .models import NotificationType, Notification
        
        notification_type, _ = NotificationType.objects.get_or_create(
            name='low_stock_alert',
            defaults={'description': 'Low stock alerts'}
        )
        
        title = "Low Stock Alert"
        message = f"Warning: {product_name} is running low. Current stock: {current_stock} units."
        
        notifications = []
        for user in staff_users:
            notifications.append(Notification(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                channel='PUSH',
                priority='HIGH',
                data={
                    'product_name': product_name,
                    'current_stock': current_stock
                }
            ))
        
        return Notification.objects.bulk_create(notifications)