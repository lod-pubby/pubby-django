from django.contrib import admin
from django.urls import path, include, re_path

from . import views

app_name = "pubby"

urlpatterns = [
    re_path(r'^(?P<path>.+)$', views.get, name='get'),
]
