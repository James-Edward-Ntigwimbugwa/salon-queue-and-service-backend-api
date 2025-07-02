from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('sales/', views.SalesReportListView.as_view(), name='sales_report_list'),
    path('inventory/', views.InventoryReportListView.as_view(), name='inventory_report_list'),
]
