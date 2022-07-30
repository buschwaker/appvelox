from django.contrib.auth import get_user_model
from django.db import models

from datetime import datetime, timezone

User = get_user_model()


class Task(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор задачи', related_name='tasks')
    title = models.CharField(max_length=25, verbose_name='Заголовок')
    text = models.TextField(max_length=200, verbose_name='Текст')
    deadline_on = models.DateTimeField(
        null=False, verbose_name='Срок выполнения(дедлайн)'
    )
    is_done = models.BooleanField(
        null=False, default=False, verbose_name='Выполнена ли задача'
    )
    done_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Число когда задача выполнена'
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_done is True:
            self.done_at = datetime.now(timezone.utc)
        super().save(*args, **kwargs)

    @property
    def is_failed(self):
        return bool(
            self.is_done is False
            and self.deadline_on < datetime.now(timezone.utc)
        )

    is_failed.fget.short_description = 'Прошел ли срок выполнения задачи'

    class Meta:
        verbose_name_plural = 'Задачи'
        verbose_name = 'Задача'
        ordering = ('is_done', 'deadline_on')
