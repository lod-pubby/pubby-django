import logging

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect


# Create your views here.
def index(request):
    # render the sparql endpoint from templates/sparql/sparql_endpoint.html
    logging.debug("sparql_endpoint")
    return render(request, 'sparql/endpoint.html', {})
