from rest_framework import serializers
from .models import (
    Notification, NotificationType, NotificationTemplate,
    UserNotificationPreference, NotificationLog
)

class NotificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationType
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    notification_type_name = serializers.CharField(source='notification_type.name', read_only=True)
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'channel', 'priority', 'status',
            'notification_type_name', 'data', 'created_at', 'scheduled_at',
            'sent_at', 'read_at', 'expires_at', 'time_since_created'
        ]
        read_only_fields = ['sent_at', 'read_at']
    
    def get_time_since_created(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'user', 'notification_type', 'title', 'message', 'channel',
            'priority', 'data', 'scheduled_at', 'expires_at'
        ]

class NotificationTemplateSerializer(serializers.ModelSerializer):
    notification_type_name = serializers.CharField(source='notification_type.name', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'

class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        exclude = ['user']

class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = '__all__'

class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for sending bulk notifications"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of user IDs to send notification to"
    )
    notification_type = serializers.PrimaryKeyRelatedField(queryset=NotificationType.objects.all())
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    channel = serializers.ChoiceField(choices=Notification.CHANNEL_CHOICES, default='PUSH')
    priority = serializers.ChoiceField(choices=Notification.PRIORITY_CHOICES, default='MEDIUM')
    data = serializers.JSONField(required=False, default=dict)
    scheduled_at = serializers.DateTimeField(required=False)

class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_status = serializers.DictField()
    recent_notifications = NotificationSerializer(many=True)