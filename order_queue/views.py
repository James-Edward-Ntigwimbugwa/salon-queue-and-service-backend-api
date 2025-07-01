# queue/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Queue, Booking, BookingService
from .serializers import (
    QueueSerializer, 
    BookingSerializer, 
    BookingCreateSerializer,
    QueueUpdateSerializer,
    QueuePositionSerializer,
    CustomerQueueStatusSerializer
)
from notifications.utils import send_queue_notification

class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        booking = serializer.save()
        return booking

class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return Booking.objects.all().order_by('-created_at')
        return Booking.objects.filter(customer=user).order_by('-created_at')

class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return Booking.objects.all()
        return Booking.objects.filter(customer=user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if booking.is_confirmed:
        return Response({'error': 'Booking already confirmed'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Confirm booking and add to queue
    queue_item = booking.confirm_booking()
    
    # Send notification
    send_queue_notification(
        user=request.user,
        message=f"Booking confirmed! You are #{queue_item.position_in_queue} in queue.",
        notification_type='booking_confirmed'
    )
    
    return Response({
        'message': 'Booking confirmed and added to queue',
        'queue_position': queue_item.position_in_queue,
        'estimated_wait_time': queue_item.estimated_wait_time
    }, status=status.HTTP_200_OK)

class QueueListView(generics.ListAPIView):
    serializer_class = QueueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return Queue.objects.all().order_by('time_joined')
        return Queue.objects.filter(customer=user)

class ActiveQueueView(generics.ListAPIView):
    serializer_class = QueueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Queue.objects.get_active_queue()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def customer_queue_status(request):
    """Get current customer's queue status"""
    try:
        queue_item = Queue.objects.get(customer=request.user, status='waiting')
        serializer = CustomerQueueStatusSerializer(queue_item)
        return Response(serializer.data)
    except Queue.DoesNotExist:
        return Response({'message': 'Not in queue'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def queue_position(request):
    """Get customer's position in queue"""
    try:
        queue_item = Queue.objects.get(customer=request.user, status='waiting')
        position = queue_item.position_in_queue
        estimated_wait = queue_item.estimated_wait_time
        total_customers = Queue.objects.get_active_queue().count()
        
        data = {
            'position': position,
            'estimated_wait_time': estimated_wait,
            'customers_ahead': position - 1 if position else 0,
            'total_customers': total_customers
        }
        
        serializer = QueuePositionSerializer(data)
        return Response(serializer.data)
    except Queue.DoesNotExist:
        return Response({'message': 'Not in queue'}, status=status.HTTP_404_NOT_FOUND)

# Admin/Staff Views
class QueueManagementView(generics.ListAPIView):
    serializer_class = QueueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role not in ['admin', 'staff']:
            return Queue.objects.none()
        return Queue.objects.all().order_by('time_joined')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_service(request, queue_id):
    """Start service for a queue item (Admin/Staff only)"""
    if request.user.role not in ['admin', 'staff']:
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    queue_item = get_object_or_404(Queue, id=queue_id)
    
    if queue_item.status != 'waiting':
        return Response({'error': 'Service cannot be started'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    queue_item.start_service(staff_member=request.user)
    
    # Notify customer
    send_queue_notification(
        user=queue_item.customer,
        message="Your service has started!",
        notification_type='service_started'
    )
    
    return Response({'message': 'Service started'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_service(request, queue_id):
    """Complete service for a queue item (Admin/Staff only)"""
    if request.user.role not in ['admin', 'staff']:
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    queue_item = get_object_or_404(Queue, id=queue_id)
    
    if queue_item.status != 'in_progress':
        return Response({'error': 'Service is not in progress'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    queue_item.complete_service()
    
    # Award loyalty points
    customer = queue_item.customer
    total_points = sum(bs.service.loyalty_points * bs.quantity 
                      for bs in queue_item.booking.bookingservice_set.all())
    customer.loyalty_points += total_points
    customer.save()
    
    # Notify customer
    send_queue_notification(
        user=queue_item.customer,
        message=f"Service completed! You earned {total_points} loyalty points.",
        notification_type='service_completed'
    )
    
    # Notify next customer in queue
    next_queue_item = Queue.objects.get_active_queue().first()
    if next_queue_item:
        send_queue_notification(
            user=next_queue_item.customer,
            message="You're next in line! Please get ready.",
            notification_type='queue_next'
        )
    
    return Response({'message': 'Service completed'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_queue_item(request, queue_id):
    """Cancel a queue item"""
    queue_item = get_object_or_404(Queue, id=queue_id)
    
    # Check permissions
    if request.user != queue_item.customer and request.user.role not in ['admin', 'staff']:
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    if queue_item.status in ['completed', 'cancelled']:
        return Response({'error': 'Cannot cancel this item'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    queue_item.cancel_service()
    
    # Notify customer if cancelled by staff
    if request.user != queue_item.customer:
        send_queue_notification(
            user=queue_item.customer,
            message="Your booking has been cancelled.",
            notification_type='booking_cancelled'
        )
    
    return Response({'message': 'Queue item cancelled'}, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_queue_item(request, queue_id):
    """Update queue item (Admin/Staff only)"""
    if request.user.role not in ['admin', 'staff']:
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    queue_item = get_object_or_404(Queue, id=queue_id)
    serializer = QueueUpdateSerializer(queue_item, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)