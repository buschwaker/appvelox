from datetime import datetime, timezone, timedelta
from time import sleep

from django.urls import reverse

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase

from tasks.models import User, Task


class TestView(APITestCase):

    def setUp(self):
        user_test1 = User.objects.create_user(
            username='test1', password='test1'
        )
        user_test1.save()
        self.user_test2 = User.objects.create_user(
            username='test2', password='test2'
        )
        self.user_test2.save()
        self.task = Task.objects.create(
            title='test task', text='test text', author=user_test1,
            deadline_on=datetime.now(timezone.utc) + timedelta(days=0.9)
        )
        self.ready_to_done = Task.objects.create(
            title='ready_to_done', text='ready_to_done', author=user_test1,
            deadline_on=datetime.now(timezone.utc) + timedelta(days=1.1)
        )
        self.already_done = Task.objects.create(
            title='already_done', text='already_done', author=user_test1,
            deadline_on=datetime.now(timezone.utc) + timedelta(days=1.1),
            is_done=True
        )
        self.ready_to_delete = Task.objects.create(
            title='ready_to_delete', text='ready_to_delete',
            author=user_test1,
            deadline_on=datetime.now(timezone.utc) + timedelta(days=1.1)
        )
        self.task_failed = Task.objects.create(
            title='task_failed', text='task_failed', author=user_test1,
            deadline_on=datetime.now(timezone.utc) + timedelta(seconds=0.15)
        )
        sleep(0.35)
        self.token_user1 = RefreshToken.for_user(user_test1).access_token
        self.token_user2 = RefreshToken.for_user(self.user_test2).access_token
        self.get_data = [
            reverse('api:task-list'),
            reverse('api:task-detail', kwargs={'pk': f'{self.task.id}'}),
            reverse('api:task-urgent'), reverse('api:task-done'),
            reverse('api:task-failed'),
        ]
        self.data_for_post = {
            'title': 'Task to post',
            'text': 'Task to post',
            'deadline_on': datetime.now(timezone.utc) + timedelta(days=1)
        }
        self.get_fields = (
            'id', 'title', 'text', 'deadline_on',
            'is_done', 'is_failed', 'done_at', 'author'
        )

    def test_get(self):
        """Смоук-тесты для GET эндпоинтов проекта"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        for data in self.get_data:
            with self.subTest(data=data):
                response = self.client.get(data)
                self.assertEqual(
                    response.status_code, 200,
                    f'Эндпоинт {data} возвращает {response.status_code}'
                )

    def test_post_request(self):
        """Тестирует, при POST запросе к /api/tasks/ с
        обязательными параметрами в БД создается задача
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        count_before = Task.objects.count()
        self.client.post(
            reverse('api:task-list'), data=self.data_for_post, format='json'
        )
        self.assertEqual(
            count_before + 1, Task.objects.count(), 'Запись в БД не создана'
        )

    def test_get_list_not_seen_by_outsiders(self):
        """Тестирует, при POST запросе к /api/tasks/ одним пользователем
        задача не доступна другому пользователю при GET запросе к /api/tasks/
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user2)
        )
        response = self.client.get(reverse('api:task-list'))
        tasks_seen_by_outsider = len(response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        self.client.post(
            reverse('api:task-list'), data=self.data_for_post, format='json'
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user2)
        )
        response = self.client.get(reverse('api:task-list'))
        self.assertEqual(
            tasks_seen_by_outsider,
            len(response.data),
            'Число записей изменилось'
        )

    def test_task_done(self):
        """Тестирует, при PATCH запросе к /api/tasks/{id_task}/task_done/
        задача становится доступной по api/tasks/done/
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.get(reverse('api:task-done'))
        tasks_seen_before = len(response.data)
        self.client.patch(
            reverse('api:task-dt', kwargs={'pk': f'{self.ready_to_done.pk}'})
        )
        response = self.client.get(reverse('api:task-done'))
        self.assertEqual(
            tasks_seen_before + 1, len(response.data),
            'Число на /done/ при PATCH запросе к '
            '/api/tasks/{id_task}/task_done/ должно было быть увеличено на 1')

    def test_task_done_on_failed(self):
        """Тестирует, при PATCH запросе к /api/tasks/{id_task}/task_done/
        нельзя проваленную задачу отметить как выполненную
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.patch(
            reverse('api:task-dt', kwargs={'pk': f'{self.task_failed.pk}'})
        )
        self.assertEqual(
            response.status_code, 400,
            f'при PATCH запросе к /api/tasks/<id_task>/task_done/ '
            f'возвращено {response.status_code} вместо 400')

    def test_task_done_on_done(self):
        """Тестирует, при PATCH запросе к /api/tasks/{id_task}/task_done/
        нельзя выполненную задачу отметить как выполненную снова
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.patch(
            reverse('api:task-dt',
                    kwargs={'pk': f'{self.already_done.pk}'})
        )
        self.assertEqual(
            response.status_code, 400,
            f'при PATCH запросе к /api/tasks/<id_task>/task_done/ '
            f'возвращено {response.status_code} вместо 400')

    def test_delete_by_outsider(self):
        """Тестирует, при DELETE запросе к /api/tasks/{id_task}/ пользователь,
        которые не создавал данную задачу не может её удалить
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user2)
        )
        response = self.client.delete(
            reverse(
                'api:task-detail',
                kwargs={'pk': f'{self.ready_to_delete.pk}'}
            )
        )
        self.assertEqual(response.status_code, 404,
                         f'при DELETE запросе к /api/tasks/<id_task>'
                         f'возвращено {response.status_code} вместо 404')

    def task_delete_by_owner(self):
        """Тестирует, при DELETE запросе к /api/tasks/{id_task}/ пользователь,
         создавший данную задачу может её удалить
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.delete(
            reverse(
                'api:task-detail',
                kwargs={'pk': f'{self.ready_to_delete.pk}'}
            )
        )
        self.assertEqual(
            response.status_code, 204,
            f'при DELETE запросе к /api/tasks/<id_task>'
            f'возвращено {response.status_code} вместо 204'
        )

    def test_failure_task(self):
        """Тестирует, что если срок выполнения задачи истек,
        то задача становится доступной по эндпоинту /api/tasks/failed/
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.get(reverse('api:task-failed'))
        self.assertEqual(
            len(response.data), 1,
            f'Число задач {len(response.data)} вместо 1'
        )

    def test_failure_task_by_outsiders(self):
        """Тестирует, что пользователь не видит проваленные задачи,
        созданные другим пользователем
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user2)
        )
        response = self.client.get(reverse('api:task-failed'))
        self.assertEqual(
            len(response.data), 0,
            f'Число задач {len(response.data)} вместо 0')

    def test_urgent_task(self):
        """Тестирует, что если до срока выполнения задачи меньше суток,
        то задача становится доступной по эндпоинту /api/tasks/urgent/
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.get(reverse('api:task-urgent'))
        self.assertEqual(
            len(response.data), 1,
            f'Число задач {len(response.data)} вместо 1'
        )

    def test_urgent_task_by_outsiders(self):
        """Тестирует, что пользователь не видит срочные задачи,
        созданные другим пользователем
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user2)
        )
        response = self.client.get(reverse('api:task-urgent'))
        self.assertEqual(
            len(response.data), 0,
            f'Число задач {len(response.data)} вместо 0'
        )

    def test_can_create_task_with_wrong_author(self):
        """Тестирует что при POST запросе api/tasks/ с параметром автор
        (pk другого пользователя) значения данного поля игнорируется
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        response = self.client.post(
            reverse('api:task-list'),
            data=self.data_for_post.update(
                {'author': self.user_test2.pk}), format='json'
        )
        self.assertNotIn('author', response.data, 'В ответе есть поле автор')

    def test_get_response_fields(self):
        """Тестирует что при оправке запроса на
        эндпоинты(GET) получаем ответ, содержащий ожидаемый ряд параметров
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + str(self.token_user1)
        )
        for data in self.get_data:
            with self.subTest(data=data):
                response = self.client.get(data)
                for field in self.get_fields:
                    with self.subTest(field=field):
                        if isinstance(response.json(), list):
                            self.assertIn(
                                field,
                                response.json()[0],
                                f'В ответе при запросе'
                                f' к {data} нет поля {field}')
                        else:
                            self.assertIn(
                                field, response.json(),
                                f'В ответе при '
                                f'запросе к {data} нет поля {field}')
