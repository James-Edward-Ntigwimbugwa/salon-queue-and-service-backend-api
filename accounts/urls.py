# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('users/', views.UserListView.as_view(), name='user_list'),
]