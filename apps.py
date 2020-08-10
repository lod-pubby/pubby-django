from django.apps import AppConfig
from . import urls as pubby_urls

class PubbyConfig(AppConfig):
    name = 'pubby'
    urls = pubby_urls
