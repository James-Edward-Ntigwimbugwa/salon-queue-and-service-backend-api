from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListCreateView.as_view(), name='payment_list_create'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('transactions/', views.TransactionListCreateView.as_view(), name='transaction_list_create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
]
