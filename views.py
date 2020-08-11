from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import rdflib
from pubby.config import getconfig

# Create your views here.




def get(request, path):
    context = {}
    context["config"] = getconfig(request)
    print("rendering")
    return render(request, "pubby/page.html", context) 

