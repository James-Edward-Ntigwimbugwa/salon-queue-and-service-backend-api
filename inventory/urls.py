from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('categories/', views.ProductCategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.ProductCategoryDetailView.as_view(), name='category_detail'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
]
