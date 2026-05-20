# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator
class User(AbstractUser):
    """
    Расширенная модель пользователя
    """
    patronymic = models.CharField(
        max_length=100,
        verbose_name='Отчество',
        blank=True,
        null=True
    )
    
    birthday = models.DateField(
        verbose_name='Дата рождения',
        blank=True,
        null=True
    )
    
    email = models.EmailField(
        verbose_name='Email',
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует',
            'invalid': 'Введите корректный email адрес'
        }
    )
    
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9._-]+$',
        message='Логин может содержать только латинские буквы, цифры и символы . - _'
    )
    
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        verbose_name='Логин'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.username})"


class Bank_questions(models.Model):
    """
    Банк вопросов.
    """
    id_question = models.AutoField(primary_key=True)
    question_text = models.TextField()
    right_answer = models.CharField(max_length=255)
    incorrect_answers = models.TextField()
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')

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
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tests')
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