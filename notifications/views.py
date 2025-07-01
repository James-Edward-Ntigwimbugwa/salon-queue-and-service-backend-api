from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from .models import (
    Notification, NotificationType, NotificationTemplate,
    UserNotificationPreference, NotificationLog
)
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    NotificationTypeSerializer, NotificationTemplateSerializer,
    UserNotificationPreferenceSerializer, BulkNotificationSerializer,
    NotificationStatsSerializer
)
from .services import NotificationService

User = get_user_model()

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(notification_type__name=type_filter)
        
        # Filter by priority
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter unread only
        unread_only = self.request.query_params.get('unread_only')
        if unread_only and unread_only.lower() == 'true':
            queryset = queryset.exclude(status='READ')
        
        return queryset.select_related('notification_type')

class NotificationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationCreateView(generics.CreateAPIView):
    serializer_class = NotificationCreateSerializer
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.mark_as_read()
        return Response({'status': 'success', 'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """Mark all notifications as read for the current user"""
    updated_count = Notification.objects.filter(
        user=request.user,
        status__in=['PENDING', 'SENT', 'DELIVERED']
    ).update(status='READ', read_at=timezone.now())
    
    return Response({
        'status': 'success',
        'message': f'{updated_count} notifications marked as read'
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """Delete a specific notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.delete()
        return Response({'status': 'success', 'message': 'Notification deleted'})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for the current user"""
    user = request.user
    
    total_notifications = Notification.objects.filter(user=user).count()
    unread_notifications = Notification.objects.filter(
        user=user,
        status__in=['PENDING', 'SENT', 'DELIVERED']
    ).count()
    
    # Notifications by type
    notifications_by_type = dict(
        Notification.objects.filter(user=user)
        .values('notification_type__name')
        .annotate(count=Count('id'))
        .values_list('notification_type__name', 'count')
    )
    
    # Notifications by status
    notifications_by_status = dict(
        Notification.objects.filter(user=user)
        .values('status')
        .annotate(count=Count('id'))
        .values_list('status', 'count')
    )
    
    # Recent notifications (last 10)
    recent_notifications = Notification.objects.filter(user=user)[:10]
    
    stats_data = {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'notifications_by_type': notifications_by_type,
        'notifications_by_status': notifications_by_status,
        'recent_notifications': recent_notifications
    }
    
    serializer = NotificationStatsSerializer(stats_data)
    return Response(serializer.data)

# User Notification Preferences Views
class UserNotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        preference, created = UserNotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

# Admin Views for managing notifications
class NotificationTypeListView(generics.ListCreateAPIView):
    queryset = NotificationType.objects.all()
    serializer_class = NotificationTypeSerializer
    permission_classes = [IsAuthenticated]

class NotificationTemplateListView(generics.ListCreateAPIView):
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bulk_notification(request):
    """Send notifications to multiple users"""
    serializer = BulkNotificationSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        
        # Get users
        users = User.objects.filter(id__in=data['user_ids'])
        
        if not users.exists():
            return Response(
                {'error': 'No valid users found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create notifications
        notifications = []
        for user in users:
            notification = Notification(
                user=user,
                notification_type=data['notification_type'],
                title=data['title'],
                message=data['message'],
                channel=data['channel'],
                priority=data['priority'],
                data=data.get('data', {}),
                scheduled_at=data.get('scheduled_at', timezone.now())
            )
            notifications.append(notification)
        
        # Bulk create
        created_notifications = Notification.objects.bulk_create(notifications)
        
        # Send notifications
        notification_service = NotificationService()
        sent_count = 0
        for notification in created_notifications:
            if notification_service.send_notification(notification):
                sent_count += 1
        
        return Response({
            'status': 'success',
            'message': f'{sent_count} notifications sent out of {len(created_notifications)} created'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_template_notification(request):
    """Send notification using a template"""
    template_id = request.data.get('template_id')
    user_ids = request.data.get('user_ids', [])
    context = request.data.get('context', {})
    
    try:
        template = NotificationTemplate.objects.get(id=template_id, is_active=True)
        users = User.objects.filter(id__in=user_ids)
        
        if not users.exists():
            return Response(
                {'error': 'No valid users found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Render template
        title, message = template.render(context)
        
        # Create and send notifications
        notification_service = NotificationService()
        sent_count = 0
        
        for user in users:
            notification = Notification.objects.create(
                user=user,
                notification_type=template.notification_type,
                title=title,
                message=message,
                channel=template.default_channel,
                priority=template.default_priority,
                data=context
            )
            
            if notification_service.send_notification(notification):
                sent_count += 1
        
        return Response({
            'status': 'success',
            'message': f'{sent_count} template notifications sent'
        })
        
    except NotificationTemplate.DoesNotExist:
        return Response(
            {'error': 'Template not found'},
            status=status.HTTP_404_NOT_FOUND
        )