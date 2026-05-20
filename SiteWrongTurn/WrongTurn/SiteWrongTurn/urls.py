from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('exam/', views.exam_intro_view, name='exam_intro'),
    path('exam/start/', views.exam_start_view, name='exam_start'),
    path('exam/question/', views.exam_question_view, name='exam_question'),
    path('exam/finish/', views.exam_finish_view, name='exam_finish'),
]