"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('pubby/', include('pubby.urls', namespace="pubby")),
    path('pubby2/', include('pubby.urls', namespace="pubby2")),
    path('admin/', admin.site.urls),
    path('data/', include('pubby.urls', namespace="data")),
    path('datasets/', include('pubby.urls', namespace="datasets")),
    path('ontology/', include('pubby.urls', namespace="ontology")),
]

handler404 = 'pubby.views.custom_error_404'
handler500 = 'pubby.views.custom_error_500'
handler403 = 'pubby.views.custom_error_403'
handler400 = 'pubby.views.custom_error_400'
