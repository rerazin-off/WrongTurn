# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Users(AbstractUser):
    """
    Модель пользователя.
    """
    id_user = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField()
    login = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    admin_role = models.BooleanField(default=False)
    groups = None
    user_permissions = None
    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['name', 'last_name', 'email', 'birthday']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.last_name} {self.name}"


class Bank_questions(models.Model):
    """
    Банк вопросов.
    """
    id_question = models.AutoField(primary_key=True)
    question_text = models.TextField()
    right_answer = models.CharField(max_length=255)
    incorrect_answers = models.TextField()
    admin = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='questions')

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Банк вопросов"

    def __str__(self):
        return self.question_text[:50]


class Types(models.Model):
    """
    Справочник типов тестирования.
    """
    id_type = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=50, unique=True)  # например: "knowledge", "speed", "logic"
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Тип тестирования"
        verbose_name_plural = "Типы тестирования"

    def __str__(self):
        return self.type_name


class Testing(models.Model):
    """
    Тестирование.
    """
    TYPE_TEST_CHOICES = [
        ('exam', 'Экзамен'),
        ('training', 'Тренировка'),
        ('final', 'Итоговый'),
    ]

    id_test = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='tests')
    questions = models.ForeignKey(Bank_questions, on_delete=models.CASCADE, related_name='tests')
    start_time = models.DateTimeField(default=timezone.now)
    types_testing = models.ForeignKey(Types, on_delete=models.CASCADE, related_name='tests')  # FK на Types
    type_test = models.CharField(max_length=20, choices=TYPE_TEST_CHOICES)

    class Meta:
        verbose_name = "Тестирование"
        verbose_name_plural = "Тестирования"

    def __str__(self):
        return f"Тест #{self.id_test} - {self.id_user.login}"


class Results_testings(models.Model):
    """
    Результаты тестирования.
    """
    id_result = models.AutoField(primary_key=True)
    id_test = models.ForeignKey(Testing, on_delete=models.CASCADE, related_name='results')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    count_correct = models.IntegerField(default=0)
    count_incorrect = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Результат тестирования"
        verbose_name_plural = "Результаты тестирования"

    def __str__(self):
        return f"Результат теста #{self.id_test.id_test} - Правильно: {self.count_correct}, Ошибок: {self.count_incorrect}"