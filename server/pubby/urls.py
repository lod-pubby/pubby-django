from django.contrib import admin
from django.urls import path, include, re_path

from . import views

app_name = "pubby"

urlpatterns = [
    path('', views.index, name='index'),
    path("<path:URI>", views.get, name="get"),
]
