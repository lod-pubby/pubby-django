from django.apps import AppConfig
from pubby.config import init_config

class PubbyConfig(AppConfig):
    name = 'pubby'

    def ready(self):
        init_config()

