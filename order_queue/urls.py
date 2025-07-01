# queue/urls.py
from django.urls import path
from . import views

app_name = 'queue'

urlpatterns = [
    # Booking URLs
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    path('bookings/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<uuid:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<uuid:booking_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    
    # Queue URLs
    path('', views.QueueListView.as_view(), name='queue_list'),
    path('active/', views.ActiveQueueView.as_view(), name='active_queue'),
    path('status/', views.customer_queue_status, name='queue_status'),
    path('position/', views.queue_position, name='queue_position'),
    
    # Queue Management URLs (Admin/Staff)
    path('manage/', views.QueueManagementView.as_view(), name='queue_management'),
    path('<uuid:queue_id>/start/', views.start_service, name='start_service'),
    path('<uuid:queue_id>/complete/', views.complete_service, name='complete_service'),
    path('<uuid:queue_id>/cancel/', views.cancel_queue_item, name='cancel_queue_item'),
    path('<uuid:queue_id>/update/', views.update_queue_item, name='update_queue_item'),
]