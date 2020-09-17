from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings
import rdflib
from pubby.config import getconfig

# Create your views here.


def get_sparql(path, config):
    for ds in config["dataset"]:
        print(f"Checking Dataset {ds['datasetBase']} for matches.")
        datasetURIPattern = ds["datasetURIPattern"]
        if datasetURIPattern:
            print("Found datasetURIPattern")
            match = datasetURIPattern.fullmatch(ds["datasetBase"].str() + path)
            if match:
                print("Matched datasetURIPattern")
                raise NotImplementedError("Not yet implemented")
        useSparqlMapping = ds["useSparqlMapping"]
        if useSparqlMapping:
            uriPattern = useSparqlMapping["uriPattern"]
            match = uriPattern.fullmatch(ds["datasetBase"].str() + path)
            if match:
                print("Matched uriPattern")
                sparql = useSparqlMapping["sparqlQuery"]
                for i, group in enumerate(match.groups(), start=1):
                    sparql = sparql.replace(f"${i}", group)
                print("Generated query: " + sparql)
                return sparql





def get(request, path):
    context = {}
    context["config"] = getconfig(request)
    context["host"] = request.get_host()
    context["port"] = request.get_port()
    context["request_path"] = request.path
    context["path"] = path
    print(f"Rendering {request.path}")
    query = get_sparql(path, getconfig(request))
    print("Query: ", query)
    return render(request, "pubby/page.html", context) 


def index(request):
    config = getconfig(request)
    print(f"Index, redirecting to {config['indexResource']}")
    return redirect(config["indexResource"].str())

