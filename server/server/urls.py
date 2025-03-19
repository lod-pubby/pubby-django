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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap

from pubby.views import SitemapGenerator

import sparql

sitemaps = {'generic': SitemapGenerator}

app_name = 'server'

urlpatterns = [
    path('pubby/', include('pubby.urls', namespace="pubby")),
    path('pubby2/', include('pubby.urls', namespace="pubby2")),
    path('admin/', admin.site.urls),
    path('sparql/', include('sparql.urls'), name="sparql"),
    path('sparql.html', sparql.views.index, name="index"),
    path('data/', include('pubby.urls', namespace="data")),
    path('datasets/', include('pubby.urls', namespace="datasets")),
    path('ontology/', include('pubby.urls', namespace="ontology")),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('sitemap.xml', sitemap,
         {'sitemaps': {'data' : SitemapGenerator}},
         name='django.contrib.sitemaps.views.sitemap')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'pubby.views.custom_error_404'
handler500 = 'pubby.views.custom_error_500'
handler403 = 'pubby.views.custom_error_403'
handler400 = 'pubby.views.custom_error_400'
