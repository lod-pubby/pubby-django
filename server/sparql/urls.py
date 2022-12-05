from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from django.views.static import serve

from . import views

app_name = "sparql"

urlpatterns = [
    path('', views.index, name='index'),
    path('sparql.html', views.index, name='index'),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
