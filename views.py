from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.conf import settings
import rdflib
from pubby.config import getconfig

# Create your views here.




def get(request, path):
    context = {}
    context["config"] = getconfig(request)
    context["host"] = request.get_host()
    context["port"] = request.get_port()
    context["request_path"] = request.path
    context["path"] = path
    print("rendering")
    return render(request, "pubby/page.html", context) 


def index(request):
    config = getconfig(request)
    print(f"Index, redirecting to {config['indexResource']}")
    return HttpResponseRedirect(str(config["indexResource"]).encode('utf-8'))

