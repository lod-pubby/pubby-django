from django.http import HttpResponse
from django.urls import resolve
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import rdflib

# Create your views here.

def getconfig(request):
    conf_file = settings.PUBBY_CONFIG
    r = resolve(request.path)
    if type(conf_file) != str:
        if not r.namespace in conf_file:
            raise ImproperlyConfigured(f"Bad setting for PUBBY_CONFIG: {conf_file}")
        conf_file = conf_file[r.namespace]
    g = rdflib.Graph()
    with open(conf_file, "r", encoding="utf-8") as f:
        g.parse(f, format="turtle")
    return g



def get(request, path):
    conf = getconfig(request)
    return HttpResponse(f"{path} | {conf.serialize(format='ttl')}")

