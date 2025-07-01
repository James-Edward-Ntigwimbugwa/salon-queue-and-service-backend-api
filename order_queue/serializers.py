# queue/serializers.py
from rest_framework import serializers
from .models import Queue, Booking, BookingService
from services.serializers import ServiceSerializer
from accounts.serializers import UserSerializer

class BookingServiceSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.ReadOnlyField()
    total_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = BookingService
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    booking_services = BookingServiceSerializer(source='bookingservice_set', many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('customer', 'total_amount', 'total_duration', 'is_confirmed')

class BookingCreateSerializer(serializers.ModelSerializer):
    services = serializers.ListField(write_only=True)
    
    class Meta:
        model = Booking
        fields = ('preferred_date', 'special_requests', 'services')
    
    def create(self, validated_data):
        services_data = validated_data.pop('services')
        booking = Booking.objects.create(
            customer=self.context['request'].user,
            **validated_data
        )
        
        # Add services to booking
        for service_data in services_data:
            service_id = service_data.get('service_id')
            quantity = service_data.get('quantity', 1)
            notes = service_data.get('notes', '')
            
            BookingService.objects.create(
                booking=booking,
                service_id=service_id,
                quantity=quantity,
                notes=notes
            )
        
        # Calculate totals
        booking.calculate_totals()
        return booking

class QueueSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    booking = BookingSerializer(read_only=True)
    position_in_queue = serializers.ReadOnlyField()
    estimated_wait_time = serializers.ReadOnlyField()
    total_service_duration = serializers.ReadOnlyField()
    staff_assigned_name = serializers.CharField(source='staff_assigned.get_full_name', read_only=True)
    
    class Meta:
        model = Queue
        fields = '__all__'

class QueueUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ('status', 'notes', 'staff_assigned')

class QueuePositionSerializer(serializers.Serializer):
    position = serializers.IntegerField()
    estimated_wait_time = serializers.IntegerField()
    customers_ahead = serializers.IntegerField()
    total_customers = serializers.IntegerField()

class CustomerQueueStatusSerializer(serializers.ModelSerializer):
    position_in_queue = serializers.ReadOnlyField()
    estimated_wait_time = serializers.ReadOnlyField()
    booking = BookingSerializer(read_only=True)
    
    class Meta:
        model = Queue
        fields = ('id', 'status', 'time_joined', 'estimated_start_time', 
                 'position_in_queue', 'estimated_wait_time', 'booking', 'notes')