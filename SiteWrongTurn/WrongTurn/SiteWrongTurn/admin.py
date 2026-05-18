# admin.py

from django.contrib import admin
from .models import Users, Bank_questions, Types, Testing, Results_testings


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'login', 'last_name', 'name', 'email', 'admin_role', 'is_active')
    list_filter = ('admin_role', 'is_active')
    search_fields = ('login', 'last_name', 'name', 'email')
    list_editable = ('admin_role',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('login', 'password', 'name', 'last_name', 'patronymic', 'birthday', 'email')
        }),
        ('Права доступа', {
            'fields': ('admin_role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Bank_questions)
class BankQuestionsAdmin(admin.ModelAdmin):
    list_display = ('id_question', 'question_text_short', 'right_answer', 'admin', 'get_admin_name')
    list_filter = ('admin',)
    search_fields = ('question_text', 'right_answer')
    raw_id_fields = ('admin',)
    
    def question_text_short(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    question_text_short.short_description = "Текст вопроса"
    
    def get_admin_name(self, obj):
        return f"{obj.admin.last_name} {obj.admin.name}" if obj.admin else "-"
    get_admin_name.short_description = "Кто добавил"


@admin.register(Types)
class TypesAdmin(admin.ModelAdmin):
    list_display = ('id_type', 'type_name', 'description_short')
    search_fields = ('type_name',)
    
    def description_short(self, obj):
        return obj.description[:100] if obj.description else "-"
    description_short.short_description = "Описание"


@admin.register(Testing)
class TestingAdmin(admin.ModelAdmin):
    list_display = ('id_test', 'id_user', 'questions_short', 'types_testing', 'type_test', 'start_time')
    list_filter = ('type_test', 'types_testing', 'start_time')
    search_fields = ('id_user__login', 'id_user__last_name', 'questions__question_text')
    raw_id_fields = ('id_user', 'questions', 'types_testing')
    date_hierarchy = 'start_time'
    
    def questions_short(self, obj):
        return obj.questions.question_text[:50] + '...' if len(obj.questions.question_text) > 50 else obj.questions.question_text
    questions_short.short_description = "Вопрос"


@admin.register(Results_testings)
class ResultsTestingsAdmin(admin.ModelAdmin):
    list_display = ('id_result', 'id_test', 'start_time', 'end_time', 'duration', 'count_correct', 'count_incorrect', 'total_questions', 'success_percent')
    list_filter = ('start_time',)
    search_fields = ('id_test__id_user__login', 'id_test__id_user__last_name')
    raw_id_fields = ('id_test',)
    readonly_fields = ('duration', 'total_questions', 'success_percent')
    
    def duration(self, obj):
        if obj.end_time and obj.start_time:
            delta = obj.end_time - obj.start_time
            minutes = delta.total_seconds() // 60
            seconds = delta.total_seconds() % 60
            return f"{int(minutes)} мин {int(seconds)} сек"
        return "-"
    duration.short_description = "Длительность"
    
    def total_questions(self, obj):
        return obj.count_correct + obj.count_incorrect
    total_questions.short_description = "Всего вопросов"
    
    def success_percent(self, obj):
        total = obj.count_correct + obj.count_incorrect
        if total > 0:
            percent = (obj.count_correct / total) * 100
            return f"{percent:.1f}%"
        return "0%"
    success_percent.short_description = "Успеваемость"