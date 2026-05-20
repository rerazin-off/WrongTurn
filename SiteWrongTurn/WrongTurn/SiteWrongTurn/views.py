from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from .forms import RegistrationForm, LoginForm
from .models import User


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
            # Вывод ошибок формы
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
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Попытка найти пользователя по email
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        except User.DoesNotExist:
            username = username_or_email
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            
            # Обработка "Запомнить меня"
            if not request.POST.get('remember'):
                request.session.set_expiry(0)
            
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль. Пожалуйста, проверьте введенные данные.')
    
    return render(request, 'login.html', {'next': request.GET.get('next', '')})


def home(request):
    """
    Главная страница после авторизации
    """
    return render(request, 'home.html')