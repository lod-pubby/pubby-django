from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from pubby.config import getconfig
from SPARQLWrapper import SPARQLWrapper, JSONLD, JSON
from rdflib import URIRef, BNode, Literal

# Create your views here.

class Resource:
    def __init__(self, request, request_path):
        self.config = getconfig(request)
        print("----------------------"+repr(self.config))
        # Important: use consistent terminology
        # The original path where we have to create a response. Can be either the same as resource, page or data path.
        self.request_path = request_path
        # The path representing the resource URI, e.g. http://dbpedia.org/resource/Berlin
        self.resource_path = ""
        # The path representing the HTML description, e.g. http://dbpedia.org/page/Berlin
        self.page_path = ""
        # The path representing the data description, e.g. http://dbpedia.org/data/Berlin
        self.data_path = ""
        # The full URI of the resource
        self.resource_uri = ""
        # The Dataset Base
        self.dataset_base = ""
        # The Web Base, i.e. the full URI to this pubby instance
        self.web_base = self.config["webBase"].str()
        # The Sparql query used to populate this resource
        self.sparql_query = ""
        # The Sparql endpoint to be used
        self.sparql_endpoint = ""
        #
        self.graph_label_predicate = ""

        # Find matching dataset in configuration
        for ds in self.config["dataset"]:
            # Cut the prefix
            if request_path.startswith(ds["webDataPrefix"]):
                path_suffix = request_path[len(ds["webDataPrefix"]):]
            elif request_path.startswith(ds["webPagePrefix"]):
                path_suffix = request_path[len(ds["webPagePrefix"]):]
            elif request_path.startswith(ds["webResourcePrefix"]):
                path_suffix = request_path[len(ds["webResourcePrefix"]):]

            # Create all possible paths. So far these are only candidates
            self.resource_path = ds["webResourcePrefix"] + path_suffix
            self.data_path = ds["webDataPrefix"] + path_suffix
            self.page_path = ds["webPagePrefix"] + path_suffix
            self.resource_uri = URIRef(ds["datasetBase"].str() + self.resource_path)
            self.dataset_base = ds["datasetBase"].str()
            self.sparql_endpoint = str(ds["sparqlEndpoint"])
            if self.sparql_endpoint == "default":
                self.sparql_endpoint = str(self.config["defaultEndpoint"])
            self.graph_label_predicate = [URIRef(item.str()) for item in ds["graphLabelPredicate"]]

            print(f"Checking Dataset {ds['datasetBase']} for matches.")
            datasetURIPattern = ds["datasetURIPattern"]
            if datasetURIPattern:
                print("Found datasetURIPattern")
                match = datasetURIPattern.fullmatch(self.resource_uri)
                if match:
                    print("Matched datasetURIPattern")
                    self.sparql_query = f"DESCRIBE <{self.resource_uri}>"
                    return
            useSparqlMapping = ds["useSparqlMapping"]
            if useSparqlMapping:
                uriPattern = useSparqlMapping["uriPattern"]
                print(repr(uriPattern))
                match = uriPattern.fullmatch(self.resource_uri)
                if match:
                    print("Matched uriPattern")
                    sparql = useSparqlMapping["sparqlQuery"]
                    for i, group in enumerate(match.groups(), start=1):
                        sparql = sparql.replace(f"${i}", group)
                    self.sparql_query = sparql
                    return
        raise ValueError(f"No matching Dataset in configuration for {request_path}")

'''
RDFLib Serializations:

n3, nquads, nt, pretty-xml, trig, trix, turtle, xml , json-ld
'''

mime2serialisation = {
    "application/json": "json-ld",
    "application/ld+json": "json-ld",
    "application/n-triples": "nt",
    "application/rdf+n3": "n3",
    "application/rdf+xml": "xml",
    "application/turtle": "turtle",
    "application/x-turtle": "turtle",
    "application/xhtml+xml": "html",
    "application/xml": "html",
    "text/html": "html",
    "text/json": "json-ld",
    "text/n3": "n3",
    "text/plain": "nt",
    "text/rdf": "turtle",
    "text/rdf+n3": "n3",
    "text/turtle": "turtle",
    "text/x-nquads": "nquads",
    "text/xml": "xml",
}


class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303


def rewrite_URL(URL, dataset_base, web_base):
    return URL.replace(dataset_base, str(web_base))


def get(request, URI):
    resource = Resource(request, URI)
    print(resource.sparql_query)

    accept = request.META.get("HTTP_ACCEPT").lower()
    serialization = "html"
    for mime in mime2serialisation:
        if mime in accept:
            serialization = mime2serialisation[mime]
            break
    print(accept)
    print(f"Content negotiation: {serialization}")

    if resource.resource_path == resource.request_path:
        if serialization == "html":
            return HttpResponseSeeOther(resource.web_base + resource.page_path)
        else:
            return HttpResponseSeeOther(resource.web_base + resource.data_path)

    # get data from the sparql_endpoint, using JSONLD for the graph info
    sparql = SPARQLWrapper(resource.sparql_endpoint)
    sparql.setQuery(resource.sparql_query)
    sparql.setReturnFormat(JSONLD)
    result = sparql.query().convert()

    if resource.request_path == resource.data_path:
        if serialization == "html":
            serialization = "turtle"
            mime = "text/turtle"
        response = HttpResponse() 
        response.content = result.serialize(format=serialization)
        response.content_type = f"{mime};charset=utf-8"
        return response

    # print(f"Result {result.serialize()}")
    # result.serialize(destination="result.xml", format='xml')

    # transfrom the result data into more usable format.
    # since we have predicates which points towards the target and from the target
    # ( stuff -> p_in -> target -> p_out -> stuff ), we need to distinguish them.

    # returns a sorted list of labels for a given URI or Literal
    def get_labels_for(URI_or_literal, custom_label=None):
        if custom_label:
            labels = [label for _, label in
                      result.preferredLabel(URI_or_literal,
                                            labelProperties=custom_label,
                                            default=[(None, URI_or_literal)])]
        else:
            labels = [label for _, label in
                      result.preferredLabel(URI_or_literal,
                                            default=[(None, URI_or_literal)])]
        return sorted(labels)


    # create quads by predicate, and do a label lookup for each thing on hand
    quads_by_predicate = {}
    for subject_uri, predicate_uri, object_uri, graph in result.quads():
        object = None
        is_subject = True
        if subject_uri == resource.resource_uri:
            object = object_uri
        elif object_uri == resource.resource_uri:
            is_subject = False
            object = subject_uri
        else:
            # otherwise it's a label
            continue

        key = (predicate_uri, is_subject, graph.identifier)
        value = quads_by_predicate.setdefault(key, {
            "labels": get_labels_for(predicate_uri),
            "link": rewrite_URL(predicate_uri, resource.dataset_base, resource.web_base),
            "qname": resource.config.shorten(predicate_uri),
            "is_subject": is_subject,
            "objects": [],
            "graph": {"link": rewrite_URL(graph.identifier, resource.dataset_base, resource.web_base) if not isinstance(graph.identifier, BNode) else None,
                      "label": get_labels_for(graph.identifier,
                                              custom_label=resource.graph_label_predicate)
                      }
        })
        if isinstance(object, URIRef):
            value["objects"].append(
                {"link": rewrite_URL(object, resource.dataset_base, resource.web_base),
                 "qname": resource.config.shorten(predicate_uri),
                 "labels": get_labels_for(object)})
        else:
            value["objects"].append(
                {"link": None,
                 "qname": None,
                 "labels": get_labels_for(object)})

    # sort the predicates and objects so the presentation of the data does not change on a refresh
    sparql_data = sorted(quads_by_predicate.values(),
                         key=lambda item: item["labels"])
    for value in sparql_data:
        value["objects"].sort(key=lambda item: item["labels"])
        value["num_objects"] = len(value["objects"])

    context = {"resource_label": " ".join([label for label in get_labels_for(resource.resource_uri)])}
    # What is in sparql_data
    context["sparql_data"] = sparql_data
    context["URI"] = URI

    return render(request, "pubby/page.html", context)


def index(request):
    config = getconfig(request)
    print(f"Index, redirecting to {config['indexResource']}")
    return redirect(config["indexResource"].str())

