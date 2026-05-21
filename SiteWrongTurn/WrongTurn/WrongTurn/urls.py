from django.contrib import admin
from django.urls import path, include  # 👈 Добавьте include в импорт

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('SiteWrongTurn.urls')),  # 👈 Добавьте эту строку
]