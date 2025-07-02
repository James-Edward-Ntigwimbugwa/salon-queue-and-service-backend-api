from rest_framework import serializers
from .models import SalesReport, InventoryReport

class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = '__all__'

class InventoryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReport
        fields = '__all__'
