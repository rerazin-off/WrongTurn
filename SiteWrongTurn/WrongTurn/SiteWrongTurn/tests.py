import json

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .forms import RegistrationForm, ProfileForm
from .models import User, Bank_questions, Results_testings
from .testing_utils import (
    build_question_ids_for_mode,
    count_errors,
    pack_incorrect_answers,
    question_to_dict,
    should_stop_exam,
)

VALID_PASSWORD = 'Test1234!'


def registration_payload(**overrides):
    data = {
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'email': 'ivanov@example.com',
        'username': 'ivanov_user',
        'password1': VALID_PASSWORD,
        'password2': VALID_PASSWORD,
    }
    data.update(overrides)
    return data


def question_payload(**overrides):
    data = {
        'text': 'Вопрос для теста?',
        'correct': 'Да',
        'options': ['Да', 'Нет', 'Не знаю', 'Пропустить'],
    }
    data.update(overrides)
    return data


class RegistrationAuthTests(TestCase):
    """Регистрация и авторизация — 20 простых тестов."""

    # --- позитивные ---

    def test_user_appears_in_database_after_registration(self):
        response = self.client.post(reverse('register'), registration_payload())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='ivanov_user').exists())

    def test_valid_email_passes_form_validation(self):
        form = RegistrationForm(data=registration_payload(email='good.mail@domain.com'))
        self.assertTrue(form.is_valid())

    def test_registration_with_patronymic_saves_user(self):
        form = RegistrationForm(data=registration_payload(
            username='with_patronymic',
            email='patronymic@example.com',
            patronymic='Иванович',
        ))
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.patronymic, 'Иванович')

    def test_login_success_redirects_to_home(self):
        User.objects.create_user(
            username='login_user',
            email='login@example.com',
            password=VALID_PASSWORD,
        )
        response = self.client.post(reverse('login'), {
            'username': 'login_user',
            'password': VALID_PASSWORD,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_login_creates_authenticated_session(self):
        User.objects.create_user(
            username='session_user',
            email='session@example.com',
            password=VALID_PASSWORD,
        )
        self.client.post(reverse('login'), {
            'username': 'session_user',
            'password': VALID_PASSWORD,
        })
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_redirects_to_login_page(self):
        user = User.objects.create_user(
            username='logout_user',
            email='logout@example.com',
            password=VALID_PASSWORD,
        )
        self.client.login(username='logout_user', password=VALID_PASSWORD)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_register_page_opens_for_guest(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_opens_for_guest(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_strong_password_passes_validation(self):
        form = RegistrationForm(data=registration_payload(
            username='strong_pass',
            email='strong@example.com',
            password1='MyPass99!',
            password2='MyPass99!',
        ))
        self.assertTrue(form.is_valid())

    def test_authenticated_user_cannot_open_register_again(self):
        User.objects.create_user(
            username='already_in',
            email='already@example.com',
            password=VALID_PASSWORD,
        )
        self.client.login(username='already_in', password=VALID_PASSWORD)
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    # --- негативные ---

    def test_short_password_does_not_create_user(self):
        form = RegistrationForm(data=registration_payload(
            username='short_pass',
            email='short@example.com',
            password1='short1',
            password2='short1',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)
        self.assertFalse(User.objects.filter(username='short_pass').exists())

    def test_missing_first_name_is_invalid(self):
        data = registration_payload()
        del data['first_name']
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_missing_last_name_is_invalid(self):
        data = registration_payload()
        del data['last_name']
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

    def test_missing_email_is_invalid(self):
        data = registration_payload()
        del data['email']
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_email_format_is_rejected(self):
        form = RegistrationForm(data=registration_payload(
            username='bad_email',
            email='not-an-email',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch_is_rejected(self):
        form = RegistrationForm(data=registration_payload(
            username='mismatch',
            email='mismatch@example.com',
            password2='Other999!',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_password_without_uppercase_is_rejected(self):
        form = RegistrationForm(data=registration_payload(
            username='no_upper',
            email='noupper@example.com',
            password1='lowercase1!',
            password2='lowercase1!',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username='taken_name',
            email='first@example.com',
            password=VALID_PASSWORD,
        )
        form = RegistrationForm(data=registration_payload(
            username='taken_name',
            email='second@example.com',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(
            username='wrong_pass',
            email='wrong@example.com',
            password=VALID_PASSWORD,
        )
        response = self.client.post(reverse('login'), {
            'username': 'wrong_pass',
            'password': 'Wrong999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_with_unknown_username_fails(self):
        response = self.client.post(reverse('login'), {
            'username': 'nobody_here',
            'password': VALID_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class AdminToolsTests(TestCase):
    """Инструменты администратора — 20 простых тестов."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@example.com',
            password=VALID_PASSWORD,
            is_staff=True,
        )
        self.admin_client = Client()
        self.admin_client.login(username='admin_test', password=VALID_PASSWORD)

        self.regular = User.objects.create_user(
            username='user_test',
            email='user@example.com',
            password=VALID_PASSWORD,
            is_staff=False,
        )
        self.user_client = Client()
        self.user_client.login(username='user_test', password=VALID_PASSWORD)

        self.guest_client = Client()

    def _post_json(self, client, url_name, payload, **kwargs):
        return client.post(
            reverse(url_name, kwargs=kwargs.get('url_kwargs', {})),
            data=json.dumps(payload),
            content_type='application/json',
        )

    # --- позитивные ---

    def test_admin_can_add_question_to_database(self):
        response = self._post_json(
            self.admin_client, 'api_question_add', question_payload(
                text='Тестовый вопрос ПДД?',
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Bank_questions.objects.filter(question_text='Тестовый вопрос ПДД?').exists()
        )

    def test_json_upload_creates_questions_in_database(self):
        payload = {
            'questions': [
                {
                    'text': 'Вопрос из JSON 1',
                    'correct': 'A',
                    'options': ['A', 'B', 'C', 'D'],
                },
                {
                    'text': 'Вопрос из JSON 2',
                    'correct': 'B',
                    'options': ['A', 'B', 'C'],
                },
            ],
        }
        response = self._post_json(
            self.admin_client, 'api_questions_upload', payload,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['created'], 2)
        self.assertEqual(
            Bank_questions.objects.filter(
                question_text__in=['Вопрос из JSON 1', 'Вопрос из JSON 2'],
            ).count(),
            2,
        )

    def test_admin_can_list_questions(self):
        Bank_questions.objects.create(
            question_text='Список вопросов',
            right_answer='Да',
            incorrect_answers='Нет|||Может|||',
            admin=self.admin,
        )
        response = self.admin_client.get(reverse('api_questions'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data['questions']), 1)

    def test_admin_can_edit_question(self):
        q = Bank_questions.objects.create(
            question_text='Старый текст',
            right_answer='Да',
            incorrect_answers='Нет|||Может|||',
            admin=self.admin,
        )
        response = self._post_json(
            self.admin_client,
            'api_question_edit',
            {
                'text': 'Новый текст',
                'correct': 'Нет',
                'options': ['Да', 'Нет', 'Может', 'Пропустить'],
            },
            url_kwargs={'pk': q.id_question},
        )
        self.assertEqual(response.status_code, 200)
        q.refresh_from_db()
        self.assertEqual(q.question_text, 'Новый текст')
        self.assertEqual(q.right_answer, 'Нет')

    def test_admin_can_delete_question(self):
        q = Bank_questions.objects.create(
            question_text='На удаление',
            right_answer='A',
            incorrect_answers='B|||C|||D|||',
            admin=self.admin,
        )
        pk = q.id_question
        response = self.admin_client.post(
            reverse('api_question_delete', kwargs={'pk': pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Bank_questions.objects.filter(id_question=pk).exists())

    def test_add_question_returns_success_flag(self):
        response = self._post_json(
            self.admin_client,
            'api_question_add',
            question_payload(text='Ответ API add'),
        )
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['question']['text'], 'Ответ API add')

    def test_json_upload_returns_created_count(self):
        response = self._post_json(
            self.admin_client,
            'api_questions_upload',
            {'questions': []},
        )
        self.assertEqual(response.json()['created'], 0)

    def test_edit_question_returns_updated_data(self):
        q = Bank_questions.objects.create(
            question_text='До правки',
            right_answer='1',
            incorrect_answers='2|||3|||4|||',
            admin=self.admin,
        )
        response = self._post_json(
            self.admin_client,
            'api_question_edit',
            {
                'text': 'После правки',
                'correct': '1',
                'options': ['1', '2', '3', '4'],
            },
            url_kwargs={'pk': q.id_question},
        )
        self.assertEqual(response.json()['question']['text'], 'После правки')

    def test_delete_question_returns_success(self):
        q = Bank_questions.objects.create(
            question_text='Удалить меня',
            right_answer='X',
            incorrect_answers='Y|||Z|||W|||',
            admin=self.admin,
        )
        response = self.admin_client.post(
            reverse('api_question_delete', kwargs={'pk': q.id_question}),
        )
        self.assertTrue(response.json()['success'])

    def test_json_upload_skips_invalid_items_but_saves_valid(self):
        payload = {
            'questions': [
                {'text': '', 'correct': 'A', 'options': ['A', 'B']},
                {
                    'text': 'Только валидный',
                    'correct': 'Да',
                    'options': ['Да', 'Нет', 'Может'],
                },
            ],
        }
        response = self._post_json(
            self.admin_client, 'api_questions_upload', payload,
        )
        self.assertEqual(response.json()['created'], 1)
        self.assertTrue(
            Bank_questions.objects.filter(question_text='Только валидный').exists(),
        )

    # --- негативные ---

    def test_non_admin_cannot_add_question(self):
        before = Bank_questions.objects.count()
        response = self._post_json(
            self.user_client,
            'api_question_add',
            question_payload(text='От обычного пользователя'),
        )
        self.assertEqual(Bank_questions.objects.count(), before)
        self.assertNotEqual(response.status_code, 200)

    def test_guest_cannot_add_question(self):
        before = Bank_questions.objects.count()
        response = self._post_json(
            self.guest_client,
            'api_question_add',
            question_payload(text='От гостя'),
        )
        self.assertEqual(Bank_questions.objects.count(), before)
        self.assertEqual(response.status_code, 302)

    def test_add_question_without_text_returns_400(self):
        response = self._post_json(
            self.admin_client,
            'api_question_add',
            question_payload(text='', correct='A', options=['A', 'B', 'C']),
        )
        self.assertEqual(response.status_code, 400)

    def test_add_question_with_too_few_options_returns_400(self):
        response = self._post_json(
            self.admin_client,
            'api_question_add',
            {'text': 'Мало вариантов', 'correct': 'A', 'options': ['A', 'B']},
        )
        self.assertEqual(response.status_code, 400)

    def test_add_question_with_invalid_json_returns_400(self):
        response = self.admin_client.post(
            reverse('api_question_add'),
            data='{broken json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_non_admin_cannot_list_questions(self):
        response = self.user_client.get(reverse('api_questions'))
        self.assertEqual(response.status_code, 302)

    def test_non_admin_cannot_delete_question(self):
        q = Bank_questions.objects.create(
            question_text='Защищённый',
            right_answer='A',
            incorrect_answers='B|||C|||D|||',
            admin=self.admin,
        )
        response = self.user_client.post(
            reverse('api_question_delete', kwargs={'pk': q.id_question}),
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(Bank_questions.objects.filter(pk=q.pk).exists())

    def test_non_admin_cannot_upload_json(self):
        response = self._post_json(
            self.user_client,
            'api_questions_upload',
            {'questions': [question_payload(text='Чужой JSON')]},
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(
            Bank_questions.objects.filter(question_text='Чужой JSON').exists(),
        )

    def test_edit_without_required_fields_returns_400(self):
        q = Bank_questions.objects.create(
            question_text='Редактировать',
            right_answer='A',
            incorrect_answers='B|||C|||D|||',
            admin=self.admin,
        )
        response = self._post_json(
            self.admin_client,
            'api_question_edit',
            {'text': '', 'correct': '', 'options': []},
            url_kwargs={'pk': q.id_question},
        )
        self.assertEqual(response.status_code, 400)

    def test_guest_cannot_upload_json(self):
        response = self._post_json(
            self.guest_client,
            'api_questions_upload',
            {
                'questions': [{
                    'text': 'Гостевой JSON',
                    'correct': 'A',
                    'options': ['A', 'B', 'C'],
                }],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Bank_questions.objects.filter(question_text='Гостевой JSON').exists(),
        )
