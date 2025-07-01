# services/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import ServiceCategory, Service, ServiceStaff, Feedback
from .serializers import (
    ServiceCategorySerializer,
    ServiceSerializer,
    ServiceDetailSerializer,
    ServiceStaffSerializer,
    FeedbackSerializer,
    FeedbackCreateSerializer
)

class ServiceCategoryListView(generics.ListCreateAPIView):
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

class ServiceCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

class ServiceListView(generics.ListCreateAPIView):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'duration', 'created_at']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

class FeedbackListView(generics.ListCreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service', 'rating']
    ordering_fields = ['rating', 'created_at']
    
    def get_queryset(self):
        return Feedback.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FeedbackCreateSerializer
        return FeedbackSerializer

class FeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'staff']:
            return Feedback.objects.all()
        return Feedback.objects.filter(customer=user)

class ServiceStaffListView(generics.ListCreateAPIView):
    queryset = ServiceStaff.objects.all()
    serializer_class = ServiceStaffSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

# Custom Permission Classes
class IsAdminOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'staff']
