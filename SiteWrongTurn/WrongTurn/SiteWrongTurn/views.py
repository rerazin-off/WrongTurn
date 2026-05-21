from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegistrationForm, LoginForm
from .models import User


def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    return user.is_authenticated and user.is_staff


def index(request):
    """
    Лендинг страница (для неавторизованных)
    """
    return render(request, 'Index.html')


@login_required
def home(request):
    """
    Главная страница после авторизации (для обычных пользователей)
    """
    # Если пользователь - администратор, перенаправляем на админ-панель
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return render(request, 'home.html')


@user_passes_test(is_admin, login_url='index')
def admin_dashboard(request):
    """
    Панель администратора (доступ только для staff)
    """
    return render(request, 'admin_dashboard.html')


@csrf_protect
@never_cache
def register_view(request):
    """
    Регистрация пользователя
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                'Регистрация прошла успешно! Теперь вы можете войти в систему.'
            )
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field != 'all':
                        label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f'{label}: {error}')
                    else:
                        messages.error(request, error)
    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {'form': form})


@csrf_protect
@never_cache
def login_view(request):
    """
    Авторизация пользователя
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            
            if not request.POST.get('remember'):
                request.session.set_expiry(0)
            
            # Перенаправление в зависимости от роли
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль. Пожалуйста, проверьте введенные данные.')
    
    return render(request, 'login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    """
    Выход из системы
    """
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')