import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.conf import settings

from .forms import RegistrationForm
from .models import User, Bank_questions, Types, Testing, Results_testings
from .testing_utils import (
    MODE_CONFIG,
    NORMAL_QUESTIONS_COUNT,
    parse_incorrect_answers,
    pack_incorrect_answers,
    question_to_dict,
    get_or_create_test_type,
    pick_random_questions,
    get_analytics_for_user,
    save_test_results,
)


def is_admin(user):
    return user.is_authenticated and user.is_staff


def index(request):
    return render(request, 'Index.html')


@login_required
def home(request):
    analytics = get_analytics_for_user(request.user)
    return render(request, 'home.html', analytics)


@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@csrf_protect
@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти в систему.')
            return redirect('login')
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

@login_required
def game_view(request):
    """Страница игры с гонками и вопросами ПДД"""
    return render(request, 'game.html')
@csrf_protect
@never_cache
def login_view(request):
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
            return redirect('home')
        messages.error(request, 'Неверный логин или пароль. Пожалуйста, проверьте введенные данные.')

    return render(request, 'login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')


# ——— Тестирование ———

@login_required
def test_intro(request, mode):
    if mode not in MODE_CONFIG:
        messages.error(request, 'Неизвестный режим тестирования.')
        return redirect('home')
    if mode != 'normal' and mode != 'exam':
        messages.info(request, 'Этот режим пока в разработке.')
        return redirect('home')

    cfg = MODE_CONFIG[mode]
    return render(request, 'test_intro.html', {
        'mode': mode,
        'title': cfg['title'],
        'description': cfg['description'],
        'questions_count': cfg['questions_count'],
    })


@login_required
def test_start(request, mode):
    if mode not in MODE_CONFIG:
        messages.error(request, 'Неизвестный режим тестирования.')
        return redirect('home')

    if mode != 'normal':
        messages.info(request, 'Сейчас доступен только обычный режим тестирования.')
        return redirect('home')

    cfg = MODE_CONFIG[mode]
    count = cfg['questions_count']
    question_ids = pick_random_questions(count)
    if not question_ids:
        total = Bank_questions.objects.count()
        messages.error(
            request,
            f'В банке недостаточно вопросов ({total} из {count}). '
            'Администратор должен добавить вопросы через «Инструменты».',
        )
        return redirect('home')

    request.session['active_test'] = {
        'mode': mode,
        'question_ids': question_ids,
        'current_index': 0,
        'answers': [],
        'start_time': timezone.now().isoformat(),
    }
    return redirect('test_question')


@login_required
def test_question(request):
    test_data = request.session.get('active_test')
    if not test_data:
        messages.error(request, 'Сессия теста не найдена. Начните тест заново.')
        return redirect('home')

    index = test_data['current_index']
    question_ids = test_data['question_ids']
    if index >= len(question_ids):
        return redirect('test_finish')

    question = get_object_or_404(Bank_questions, id_question=question_ids[index])
    q_data = question_to_dict(question)
    cfg = MODE_CONFIG.get(test_data['mode'], MODE_CONFIG['normal'])

    return render(request, 'test_question.html', {
        'question': q_data,
        'question_number': index + 1,
        'total_questions': len(question_ids),
        'mode_title': cfg['title'],
        'is_last': index >= len(question_ids) - 1,
    })


@login_required
@require_POST
def test_answer(request):
    test_data = request.session.get('active_test')
    if not test_data:
        return redirect('home')

    selected = request.POST.get('answer', '').strip()
    index = test_data['current_index']
    question_ids = test_data['question_ids']
    question = get_object_or_404(Bank_questions, id_question=question_ids[index])

    is_correct = selected == question.right_answer
    test_data['answers'].append({
        'question_id': question.id_question,
        'question_text': question.question_text,
        'selected': selected,
        'right_answer': question.right_answer,
        'is_correct': is_correct,
    })
    test_data['current_index'] = index + 1
    request.session['active_test'] = test_data
    request.session.modified = True

    if test_data['current_index'] >= len(question_ids):
        return redirect('test_finish')
    return redirect('test_question')


@login_required
def test_finish(request):
    test_data = request.session.get('active_test')
    if not test_data or not test_data.get('answers'):
        messages.error(request, 'Нет данных для сохранения результата.')
        return redirect('home')

    result = save_test_results(request.user, test_data)
    request.session['last_test_result'] = result
    del request.session['active_test']
    request.session.modified = True
    return redirect('test_results')


@login_required
def test_results(request):
    result = request.session.get('last_test_result')
    if not result:
        messages.error(request, 'Результаты теста не найдены.')
        return redirect('home')
    return render(request, 'test_results.html', {'result': result})


# ——— API администратора (банк вопросов) ———

def _question_api_item(q):
    wrong, image = parse_incorrect_answers(q.incorrect_answers)
    return {
        'id': q.id_question,
        'text': q.question_text,
        'correct': q.right_answer,
        'topic': 'Прочее',
        'image': image,
        'options': wrong + [q.right_answer],
    }


@user_passes_test(is_admin, login_url='login')
@require_http_methods(['GET'])
def api_questions_list(request):
    items = [_question_api_item(q) for q in Bank_questions.objects.all().order_by('id_question')]
    return JsonResponse({'questions': items})


@user_passes_test(is_admin, login_url='login')
@require_POST
def api_question_add(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)

    text = data.get('text', '').strip()
    correct = data.get('correct', '').strip()
    options = data.get('options', [])
    image = data.get('image', '')

    if not text or not correct or len(options) < 3:
        return JsonResponse({'error': 'Заполните вопрос, варианты и правильный ответ'}, status=400)

    wrong_options = [o for o in options if o != correct][:3]
    while len(wrong_options) < 3:
        wrong_options.append('')

    q = Bank_questions.objects.create(
        question_text=text,
        right_answer=correct,
        incorrect_answers=pack_incorrect_answers(wrong_options[:3], image),
        admin=request.user,
    )
    return JsonResponse({'success': True, 'question': _question_api_item(q)})


@user_passes_test(is_admin, login_url='login')
@require_POST
def api_question_edit(request, pk):
    question = get_object_or_404(Bank_questions, id_question=pk)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)

    text = data.get('text', '').strip()
    correct = data.get('correct', '').strip()
    options = data.get('options', [])
    image = data.get('image')
    if image is None:
        _, image = parse_incorrect_answers(question.incorrect_answers)

    if not text or not correct:
        return JsonResponse({'error': 'Заполните обязательные поля'}, status=400)

    wrong_options = [o for o in options if o != correct][:3]
    question.question_text = text
    question.right_answer = correct
    question.incorrect_answers = pack_incorrect_answers(wrong_options, image)
    question.save()
    return JsonResponse({'success': True, 'question': _question_api_item(question)})


@user_passes_test(is_admin, login_url='login')
@require_POST
def api_question_delete(request, pk):
    question = get_object_or_404(Bank_questions, id_question=pk)
    question.delete()
    return JsonResponse({'success': True})


@user_passes_test(is_admin, login_url='login')
@require_POST
def api_questions_upload_json(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON'}, status=400)

    items = data.get('questions', [])
    created = 0
    for item in items:
        text = (item.get('text') or '').strip()
        correct = (item.get('correct') or '').strip()
        options = item.get('options') or []
        if not text or not correct or len(options) < 2:
            continue
        wrong = [o for o in options if o != correct]
        if len(wrong) < 1:
            continue
        Bank_questions.objects.create(
            question_text=text,
            right_answer=correct,
            incorrect_answers=pack_incorrect_answers(wrong[:3], item.get('image', '')),
            admin=request.user,
        )
        created += 1

    return JsonResponse({'success': True, 'created': created})
