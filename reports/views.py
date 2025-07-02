from rest_framework import generics, permissions
from .models import SalesReport, InventoryReport
from .serializers import SalesReportSerializer, InventoryReportSerializer

class SalesReportListView(generics.ListAPIView):
    queryset = SalesReport.objects.all()
    serializer_class = SalesReportSerializer
    permission_classes = [permissions.IsAuthenticated]

class InventoryReportListView(generics.ListAPIView):
    queryset = InventoryReport.objects.all()
    serializer_class = InventoryReportSerializer
    permission_classes = [permissions.IsAuthenticated]
