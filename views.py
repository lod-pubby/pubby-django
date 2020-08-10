from django.http import HttpResponse
from django.conf import settings
import rdflib
from pubby.config import getconfig

# Create your views here.




def get(request, path):
    conf = getconfig(request)
    return HttpResponse(f"{path} | {conf.get('dataset').get('datasetBase')}")

