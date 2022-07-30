from django.urls import include, path


from rest_framework import routers

from .views import TaskViewSet

app_name = 'api'

router_v1 = routers.DefaultRouter()

router_v1.register('tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router_v1.urls)),
]
