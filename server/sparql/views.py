import logging
import os

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect

from server import settings


# Create your views here.
def index(request):
    # render the sparql endpoint from templates/sparql/sparql_endpoint.html
    logging.debug("sparql_endpoint")

    # get a list of all the graphs
    # iterate over the files in the path
    #path = "/data/web.judaicalink.org/judaicalink-site/content/datasets"
    path = os.path.join(settings.BASE_DIR, settings.DATASETS_DIR)

    # get the list of files
    files = os.listdir(path)
    #iterate over the files if they are .md files
    graphs = {}
    for file in files:
        if file.endswith(".md"):
            # in the markdown file get the title and the graph
            with open(path + "/" + file, 'r') as f:
                loaded = False
                lines = f.readlines()
                for line in lines:
                    if line.startswith("title ="):
                        title = line.split("=")[1].strip().replace("\"", "")
                    if line.startswith("graph ="):
                        uri = line.split("=")[1].strip().replace("\"", "")
                    if line.startswith("loaded = true"):
                        loaded = True

                if loaded:
                    graphs[title] = uri
                logging.info(msg=f'title: {title} graph: {uri}\n')

    if graphs:
        graphs = dict(sorted(graphs.items()))
        return render(request, 'sparql/endpoint.html', {'graphs': graphs})
    else:
        return render(request, 'sparql/endpoint.html', {})
