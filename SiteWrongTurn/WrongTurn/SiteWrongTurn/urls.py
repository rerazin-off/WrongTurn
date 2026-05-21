from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('test/<str:mode>/intro/', views.test_intro, name='test_intro'),
    path('test/<str:mode>/start/', views.test_start, name='test_start'),
    path('test/question/', views.test_question, name='test_question'),
    path('test/answer/', views.test_answer, name='test_answer'),
    path('test/finish/', views.test_finish, name='test_finish'),
    path('test/results/', views.test_results, name='test_results'),

    # API банка вопросов (администратор)
    path('api/questions/', views.api_questions_list, name='api_questions'),
    path('api/questions/add/', views.api_question_add, name='api_question_add'),
    path('api/questions/<int:pk>/edit/', views.api_question_edit, name='api_question_edit'),
    path('api/questions/<int:pk>/delete/', views.api_question_delete, name='api_question_delete'),
    path('api/questions/upload-json/', views.api_questions_upload_json, name='api_questions_upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
