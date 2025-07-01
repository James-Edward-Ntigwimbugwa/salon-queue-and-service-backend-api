# services/urls.py
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Service Categories
    path('categories/', views.ServiceCategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.ServiceCategoryDetailView.as_view(), name='category_detail'),
    
    # Services
    path('', views.ServiceListView.as_view(), name='service_list'),
    path('<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    # Feedback
    path('feedback/', views.FeedbackListView.as_view(), name='feedback_list'),
    path('feedback/<int:pk>/', views.FeedbackDetailView.as_view(), name='feedback_detail'),
    
    # Service Staff
    path('staff/', views.ServiceStaffListView.as_view(), name='service_staff_list'),
]