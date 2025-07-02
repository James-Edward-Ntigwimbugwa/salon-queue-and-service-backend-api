from django.db import models

class SalesReport(models.Model):
    report_date = models.DateField()
    total_sales = models.DecimalField(max_digits=15, decimal_places=2)
    total_orders = models.IntegerField()
    total_customers = models.IntegerField()
    
    def __str__(self):
        return f"Sales Report - {self.report_date}"

class InventoryReport(models.Model):
    report_date = models.DateField()
    total_products = models.IntegerField()
    low_stock_products = models.IntegerField()
    
    def __str__(self):
        return f"Inventory Report - {self.report_date}"
