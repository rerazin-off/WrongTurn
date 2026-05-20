from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
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
=======
    path('admin/', admin.site.urls),
    
    path('', views.index, name='index'),      # Лендинг (для неавторизованных)
    path('home/', views.home, name='home'),   # Личный кабинет (для авторизованных)
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
>>>>>>> 2f87ceb (Add exit from profile)
]