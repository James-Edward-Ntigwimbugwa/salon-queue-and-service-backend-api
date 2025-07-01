# services/serializers.py
from rest_framework import serializers
from .models import ServiceCategory, Service, ServiceStaff, Feedback

class ServiceCategorySerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = '__all__'
    
    def get_services_count(self, obj):
        return obj.services.filter(is_active=True).count()

class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    class Meta:
        model = Service
        fields = '__all__'

class ServiceDetailSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    staff_members = serializers.SerializerMethodField()
    recent_feedback = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = '__all__'
    
    def get_staff_members(self, obj):
        staff_assignments = ServiceStaff.objects.filter(service=obj)
        return [{
            'id': assignment.staff.id,
            'username': assignment.staff.username,
            'first_name': assignment.staff.first_name,
            'last_name': assignment.staff.last_name,
            'is_primary': assignment.is_primary
        } for assignment in staff_assignments]
    
    def get_recent_feedback(self, obj):
        recent_feedback = obj.feedback_set.order_by('-created_at')[:5]
        return FeedbackSerializer(recent_feedback, many=True).data

class ServiceStaffSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = ServiceStaff
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('customer',)
    
    def get_customer_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.customer.get_full_name() or obj.customer.username

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('service', 'rating', 'comment', 'is_anonymous')
    
    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)