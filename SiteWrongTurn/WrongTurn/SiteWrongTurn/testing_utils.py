import json
import random
from datetime import datetime
from django.utils import timezone

from .models import Bank_questions, Types, Testing, Results_testings

NORMAL_QUESTIONS_COUNT = 20

MODE_CONFIG = {
    'normal': {
        'type_name': 'Обычный',
        'type_test': 'training',
        'questions_count': 20,
        'title': 'Обычный режим',
        'description': 'Тренируйтесь, чтобы повышать уровень своих знаний! Вам будет предложено 20 случайных вопросов.',
    },
    'exam': {
        'type_name': 'Экзамен',
        'type_test': 'exam',
        'questions_count': 20,
        'title': 'Режим экзамен',
        'description': 'Попробуйте свои силы как на настоящем экзамене! Но будьте внимательны, у вас всего 2 попытки!',
    },
}


def parse_incorrect_answers(raw):
    """Разбор поля incorrect_answers: JSON, список или строка через |"""
    if not raw:
        return [], ''
    text = raw.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            answers = data.get('answers') or data.get('options') or []
            image = data.get('image') or ''
            return list(answers), image
        if isinstance(data, list):
            return data, ''
    except (json.JSONDecodeError, TypeError):
        pass
    if '|' in text:
        return [p.strip() for p in text.split('|') if p.strip()], ''
    return [text], ''


def pack_incorrect_answers(answers_list, image=''):
    payload = {'answers': answers_list}
    if image:
        payload['image'] = image
    return json.dumps(payload, ensure_ascii=False)


def question_to_dict(question, shuffle_options=True):
    wrong, image = parse_incorrect_answers(question.incorrect_answers)
    options = list(wrong) + [question.right_answer]
    if shuffle_options:
        random.shuffle(options)
    return {
        'id': question.id_question,
        'text': question.question_text,
        'right_answer': question.right_answer,
        'options': options,
        'image': image,
    }


def get_or_create_test_type(mode):
    cfg = MODE_CONFIG.get(mode, MODE_CONFIG['normal'])
    test_type, _ = Types.objects.get_or_create(
        type_name=cfg['type_name'],
        defaults={'description': cfg['description']},
    )
    return test_type, cfg


def pick_random_questions(count):
    ids = list(Bank_questions.objects.values_list('id_question', flat=True))
    if len(ids) < count:
        return None
    selected = random.sample(ids, count)
    return selected


def get_analytics_for_user(user):
    results = (
        Results_testings.objects
        .filter(id_test__id_user=user)
        .select_related('id_test__types_testing')
        .order_by('-end_time')
    )
    tests_completed = results.count()
    total_correct = sum(r.count_correct for r in results)
    total_incorrect = sum(r.count_incorrect for r in results)
    total_answers = total_correct + total_incorrect
    error_percent = round((total_incorrect / total_answers) * 100) if total_answers else 0

    history = []
    for r in results:
        test = r.id_test
        type_name = test.types_testing.type_name if test.types_testing else 'Тест'
        local_start = timezone.localtime(r.start_time)
        local_end = timezone.localtime(r.end_time)
        history.append({
            'type_name': type_name,
            'date': local_start.strftime('%d.%m.%Y'),
            'start_time': local_start.strftime('%H:%M'),
            'end_time': local_end.strftime('%H:%M'),
            'correct_count': r.count_correct,
        })

    return {
        'tests_completed': tests_completed,
        'error_percent': error_percent,
        'history': history,
    }


def save_test_results(user, session_data):
    """Сохранение результата теста в БД (без изменения схемы)."""
    answers = session_data.get('answers', [])
    question_ids = session_data.get('question_ids', [])
    mode = session_data.get('mode', 'normal')
    start_iso = session_data.get('start_time')
    start_time = datetime.fromisoformat(start_iso)
    if timezone.is_naive(start_time):
        start_time = timezone.make_aware(start_time)

    test_type, cfg = get_or_create_test_type(mode)
    correct = sum(1 for a in answers if a.get('is_correct'))
    incorrect = len(answers) - correct

    first_testing = None
    for qid in question_ids:
        question = Bank_questions.objects.get(id_question=qid)
        row = Testing.objects.create(
            id_user=user,
            questions=question,
            types_testing=test_type,
            type_test=cfg['type_test'],
            start_time=start_time,
        )
        if first_testing is None:
            first_testing = row

    end_time = timezone.now()
    Results_testings.objects.create(
        id_test=first_testing,
        start_time=start_time,
        end_time=end_time,
        count_correct=correct,
        count_incorrect=incorrect,
    )

    wrong_details = []
    for idx, ans in enumerate(answers):
        if not ans.get('is_correct'):
            wrong_details.append({
                'number': idx + 1,
                'question_text': ans.get('question_text', ''),
                'user_answer': ans.get('selected', ''),
                'correct_answer': ans.get('right_answer', ''),
            })

    return {
        'correct': correct,
        'total': len(answers),
        'wrong_details': wrong_details,
        'mode_title': cfg['title'],
    }
