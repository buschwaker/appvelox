from datetime import datetime, timedelta, timezone

from django.db.models import Q

from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from api.mixins import CreateListRetrieveView
from api.serializers import TaskSerializer
from tasks.models import Task


class TaskViewSet(CreateListRetrieveView):
    """TaskViewSet

    list: Выводит список актуальных задач

    retrieve: Выводит задачу по номеру id

    create: Создает задачу

    destroy: Удаляет задачу
    """
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, )

    def get_current_user(self):
        return self.request.user

    def get_queryset(self):
        user = self.get_current_user()
        if self.action == 'failed':
            return user.tasks.filter(
                Q(is_done__exact=False)
                & Q(deadline_on__lt=datetime.now(timezone.utc))
            ).order_by('-deadline_on')
        elif self.action == 'list':
            return user.tasks.filter(
                Q(is_done__exact=False)
                & Q(deadline_on__gt=datetime.now(timezone.utc)))
        elif self.action == 'done':
            return user.tasks.filter(
                is_done__exact=True
            ).order_by('-done_at')
        elif self.action == 'urgent':
            time_tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            return user.tasks.filter(
                Q(is_done__exact=False)
                & Q(deadline_on__gt=datetime.now(timezone.utc))
                & Q(deadline_on__lt=time_tomorrow))
        return user.tasks.all()

    def create_custom(self):
        tasks = self.get_queryset()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['patch'], url_name='dt')
    def done_task(self, request, pk=None):
        """Запрос позволяет отметить задачу как выполненную"""
        task_to_done = Task.objects.get(pk=pk)
        if task_to_done.is_failed:
            raise ParseError('Задача уже провалена!')
        elif task_to_done.is_done:
            raise ParseError('Задача уже выполнена!')
        task_to_done.is_done = True
        task_to_done.save()
        serializer = TaskSerializer(task_to_done)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Выводит список проваленных задач"""
        return self.create_custom()

    @action(detail=False, methods=['get'])
    def done(self, request):
        """Выводит список успешно выполненных задач"""
        return self.create_custom()

    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Выводит список задач,
        для которых меньше чем через день наступает дедлайн
        """
        return self.create_custom()
