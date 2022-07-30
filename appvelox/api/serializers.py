from datetime import datetime, timezone

from rest_framework import serializers

from tasks.models import Task


class TaskSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'text', 'deadline_on',
            'is_done', 'is_failed', 'done_at', 'author'
        )
        read_only_fields = ('is_done', 'done_at')

    def validate(self, data):
        if data['deadline_on'] < datetime.now(timezone.utc):
            raise serializers.ValidationError(
                'Нельзя создать задачу задним числом!'
            )
        return data
