from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from .forms import RegistrationForm, LoginForm
from .models import User


def index(request):
    """
    Лендинг страница (для неавторизованных)
    """
    return render(request, 'index.html')


def home(request):
    """
    Главная страница после авторизации
    """
    return render(request, 'home.html')


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
                    if field != '__all__':
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
            
            return redirect('home')  # Перенаправление на home
        else:
            messages.error(request, 'Неверный логин или пароль. Пожалуйста, проверьте введенные данные.')
    
    return render(request, 'login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    """
    Выход из системы
    """
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')  # Перенаправление на лендинг