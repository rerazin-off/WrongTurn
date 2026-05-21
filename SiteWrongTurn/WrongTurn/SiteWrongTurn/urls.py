from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.login_view, name='login'),                      # Лендинг
    path('home/', views.home, name='home'),                   # Личный кабинет пользователя
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),  # Панель администратора
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]