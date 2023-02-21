from django.contrib import admin
from django.urls import path, include, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "pubby"

urlpatterns = [
    path('', views.index, name='index'),
    path('create_issue', views.create_issue, name='create_issue'),
    path("<path:URI>", views.get, name="get"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "pubby.views.custom_error_404"
handler500 = "pubby.views.custom_error_500"
handler403 = "pubby.views.custom_error_403"
handler400 = "pubby.views.custom_error_400"
