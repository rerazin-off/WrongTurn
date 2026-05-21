from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import User


class RegistrationForm(UserCreationForm):
    """
    Форма регистрации
    """
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'})
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        label='Фамилия',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'})
    )
    
    patronymic = forms.CharField(
        max_length=100,
        required=False,
        label='Отчество',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванович'})
    )
    
    birthday = forms.DateField(
        required=False,
        label='Дата рождения',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ivanov@example.com'})
    )
    
    username = forms.CharField(
        max_length=150,
        required=True,
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ivanov_ivan'})
    )
    
    password1 = forms.CharField(
        required=True,
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Создайте пароль'})
    )
    
    password2 = forms.CharField(
        required=True,
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic', 'birthday')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Проверка формата email
            email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_regex.match(email):
                raise ValidationError('Введите корректный email адрес (пример: user@domain.com)')
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            errors = []
            
            if len(password) < 8:
                errors.append('Пароль должен содержать минимум 8 символов')
            
            if not re.search(r'[A-Z]', password):
                errors.append('Пароль должен содержать хотя бы одну заглавную букву (A-Z)')
            
            if not re.search(r'[a-z]', password):
                errors.append('Пароль должен содержать хотя бы одну строчную букву (a-z)')
            
            if not re.search(r'\d', password):
                errors.append('Пароль должен содержать хотя бы одну цифру (0-9)')
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append('Пароль должен содержать хотя бы один специальный символ (!@#$%^&*() и т.д.)')
            
            if not re.match(r'^[A-Za-z\d!@#$%^&*(),.?":{}|<>]+$', password):
                errors.append('Пароль должен содержать только латинские буквы, цифры и специальные символы')
            
            if errors:
                raise ValidationError(errors)
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Пароли не совпадают')
        
        return cleaned_data


class LoginForm(AuthenticationForm):
    """
    Форма авторизации
    """
    username = forms.CharField(
        label='Логин или Email',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите логин или email'
        })
    )
    
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    
    error_messages = {
        'invalid_login': 'Неверный логин или пароль. Пожалуйста, проверьте введенные данные.',
        'inactive': 'Учетная запись не активирована.',
    }