from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Order, OrderServiceItem, OrderProductItem, Cart, 
    CartServiceItem, CartProductItem, OrderStatusHistory
)
from services.serializers import ServiceSerializer

User = get_user_model()

class OrderServiceItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_duration = serializers.IntegerField(source='service.duration', read_only=True)
    
    class Meta:
        model = OrderServiceItem
        fields = [
            'id', 'service', 'service_name', 'service_duration', 
            'quantity', 'unit_price', 'subtotal', 'started_at', 
            'completed_at', 'staff_notes'
        ]
        read_only_fields = ['subtotal', 'started_at', 'completed_at']

class OrderProductItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = OrderProductItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['subtotal']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'previous_status', 'new_status', 'changed_by',
            'changed_by_name', 'notes', 'changed_at'
        ]

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.get_full_name', read_only=True)
    service_items = OrderServiceItemSerializer(many=True, read_only=True)
    product_items = OrderProductItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'customer_email',
            'order_type', 'status', 'total_amount', 'discount_amount', 
            'final_amount', 'created_at', 'updated_at', 'confirmed_at',
            'completed_at', 'cancelled_at', 'scheduled_date', 
            'estimated_duration', 'assigned_staff', 'assigned_staff_name',
            'notes', 'customer_rating', 'customer_feedback',
            'service_items', 'product_items', 'status_history'
        ]
        read_only_fields = [
            'order_number', 'total_amount', 'final_amount', 'created_at',
            'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'
        ]

class OrderCreateSerializer(serializers.ModelSerializer):
    service_items = OrderServiceItemSerializer(many=True, required=False)
    product_items = OrderProductItemSerializer(many=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'customer', 'order_type', 'scheduled_date', 'notes',
            'service_items', 'product_items'
        ]
    
    def create(self, validated_data):
        service_items_data = validated_data.pop('service_items', [])
        product_items_data = validated_data.pop('product_items', [])
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Create service items
        for item_data in service_items_data:
            service = item_data['service']
            OrderServiceItem.objects.create(
                order=order,
                service=service,
                quantity=item_data['quantity'],
                unit_price=service.price
            )
        
        # Create product items
        for item_data in product_items_data:
            product = item_data['product']
            OrderProductItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price
            )
        
        # Calculate totals
        order.calculate_total()
        
        return order

class CartServiceItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    service_duration = serializers.IntegerField(source='service.duration', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartServiceItem
        fields = [
            'id', 'service', 'service_name', 'service_price', 
            'service_duration', 'quantity', 'subtotal', 'added_at'
        ]

class CartProductItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartProductItem
        fields = [
            'id', 'product', 'product_name', 'product_price',
            'product_image', 'quantity', 'subtotal', 'added_at'
        ]

class CartSerializer(serializers.ModelSerializer):
    service_items = CartServiceItemSerializer(many=True, read_only=True)
    product_items = CartProductItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'customer', 'service_items', 'product_items',
            'total', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['customer']
    
    def get_total(self, obj):
        return obj.get_total()
    
    def get_items_count(self, obj):
        service_count = obj.service_items.count()
        product_count = obj.product_items.count()
        return service_count + product_count

class AddToCartSerializer(serializers.Serializer):
    item_type = serializers.ChoiceField(choices=['service', 'product'])
    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

class OrderRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True)

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    assigned_staff_id = serializers.IntegerField(required=False)

class OrderStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    popular_services = serializers.ListField()
    popular_products = serializers.ListField()
    orders_by_status = serializers.DictField()
    recent_orders = OrderSerializer(many=True)