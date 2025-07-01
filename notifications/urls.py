from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # User notification views
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('create/', views.NotificationCreateView.as_view(), name='notification-create'),
    path('<int:notification_id>/read/', views.mark_notification_read, name='mark-read'),
    path('mark-all-read/', views.mark_all_read, name='mark-all-read'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete-notification'),
    path('stats/', views.notification_stats, name='notification-stats'),
    
    # User preferences
    path('preferences/', views.UserNotificationPreferenceView.as_view(), name='user-preferences'),
    
    # Admin/Staff views
    path('types/', views.NotificationTypeListView.as_view(), name='notification-types'),
    path('templates/', views.NotificationTemplateListView.as_view(), name='notification-templates'),
    path('bulk-send/', views.send_bulk_notification, name='bulk-send'),
    path('template-send/', views.send_template_notification, name='template-send'),
]