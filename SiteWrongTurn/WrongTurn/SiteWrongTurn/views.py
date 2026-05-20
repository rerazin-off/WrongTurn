

import json
import random
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from .forms import RegistrationForm, LoginForm
from .models import Bank_questions, Results_testings, Testing, Types, User


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


def _parse_answers(question):
    raw_answers = question.incorrect_answers or ""
    try:
        parsed = json.loads(raw_answers)
        if isinstance(parsed, list):
            answers = [str(item).strip() for item in parsed if str(item).strip()]
        else:
            answers = [chunk.strip() for chunk in str(parsed).split("||") if chunk.strip()]
    except json.JSONDecodeError:
        chunks = raw_answers.replace("\r", "\n").replace(";", "\n").replace(",", "\n").split("\n")
        answers = [chunk.strip() for chunk in chunks if chunk.strip()]

    answers.append(question.right_answer.strip())
    unique_answers = list(dict.fromkeys(answers))
    random.shuffle(unique_answers)
    return unique_answers


@login_required
def analytics_view(request):
    results = Results_testings.objects.filter(id_test__id_user=request.user).select_related("id_test").order_by("-end_time")
    passed_tests = 0
    total_correct = 0
    total_incorrect = 0
    history = []

    for result in results:
        total_answers = result.count_correct + result.count_incorrect
        score = round((result.count_correct / total_answers) * 100) if total_answers else 0
        if score >= 80:
            passed_tests += 1
        total_correct += result.count_correct
        total_incorrect += result.count_incorrect
        history.append(
            {
                "mode": result.id_test.get_type_test_display(),
                "date": result.end_time,
                "duration": result.end_time - result.start_time,
                "correct": result.count_correct,
                "incorrect": result.count_incorrect,
                "score": score,
            }
        )

    context = {
        "passed_tests": passed_tests,
        "score_percent": round((total_correct / (total_correct + total_incorrect)) * 100) if (total_correct + total_incorrect) else 0,
        "history": history[:10],
    }
    return render(request, "analytics.html", context)


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")


@login_required
def exam_intro_view(request):
    return render(request, "exam_intro.html")


@login_required
def exam_start_view(request):
    questions = list(Bank_questions.objects.order_by("?")[:20])
    if not questions:
        messages.error(request, "В базе пока нет вопросов для тестирования.")
        return redirect("home")

    request.session["active_exam"] = {
        "question_ids": [question.id_question for question in questions],
        "index": 0,
        "correct": 0,
        "incorrect": 0,
        "start_time": Testing._meta.get_field("start_time").default().isoformat(),
        "type_test": "exam",
    }
    return redirect("exam_question")


@login_required
def exam_question_view(request):
    exam = request.session.get("active_exam")
    if not exam:
        messages.info(request, "Сначала начните тестирование.")
        return redirect("exam_intro")

    question_ids = exam.get("question_ids", [])
    index = exam.get("index", 0)
    total = len(question_ids)

    if index >= total:
        return redirect("exam_finish")

    question = get_object_or_404(Bank_questions, id_question=question_ids[index])

    if request.method == "POST":
        selected_answer = request.POST.get("answer", "").strip()
        if not selected_answer:
            messages.error(request, "Выберите один вариант ответа.")
            return redirect("exam_question")

        if selected_answer == question.right_answer.strip():
            exam["correct"] = exam.get("correct", 0) + 1
        else:
            exam["incorrect"] = exam.get("incorrect", 0) + 1

        exam["index"] = index + 1
        request.session["active_exam"] = exam
        if exam["index"] >= total:
            return redirect("exam_finish")
        return redirect("exam_question")

    context = {
        "question": question,
        "answers": _parse_answers(question),
        "question_number": index + 1,
        "total_questions": total,
    }
    return render(request, "exam_question.html", context)


@login_required
def exam_finish_view(request):
    exam = request.session.pop("active_exam", None)
    if not exam:
        return redirect("home")

    type_obj, _ = Types.objects.get_or_create(
        type_name="Экзамен",
        defaults={"description": "Классический режим экзамена"},
    )
    question_ids = exam.get("question_ids", [])
    first_question = get_object_or_404(Bank_questions, id_question=question_ids[0])
    start_time = Testing._meta.get_field("start_time").to_python(exam["start_time"])
    testing = Testing.objects.create(
        id_user=request.user,
        questions=first_question,
        start_time=start_time,
        types_testing=type_obj,
        type_test=exam.get("type_test", "exam"),
    )
    end_time = Testing._meta.get_field("start_time").default()

    result = Results_testings.objects.create(
        id_test=testing,
        start_time=start_time,
        end_time=end_time,
        count_correct=exam.get("correct", 0),
        count_incorrect=exam.get("incorrect", 0),
    )

    total = result.count_correct + result.count_incorrect
    score = round((result.count_correct / total) * 100) if total else 0
    duration = end_time - start_time
    context = {
        "score": score,
        "correct": result.count_correct,
        "incorrect": result.count_incorrect,
        "duration": str(duration).split(".")[0] if isinstance(duration, timedelta) else duration,
    }
    return render(request, "exam_result.html", context)

