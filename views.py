from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from pubby.config import getconfig
from SPARQLWrapper import SPARQLWrapper, XML, JSONLD
from rdflib import Graph, URIRef, Literal

# Create your views here.


def get(request, URI):
    # get config
    config = getconfig(request)
    sparql_query = config["dataset"][0]["useSparqlMapping"]["sparqlQuery"]
    dataset_base = config["dataset"][0]["datasetBase"]
    sparql_endpoint = str(config["dataset"][0]["sparqlEndpoint"])
    uri_pattern = str(config["dataset"][0]["useSparqlMapping"]["uriPattern"])
    if sparql_endpoint == "default":
        sparql_endpoint = str(config["defaultEndpoint"])

    # add sparql_query to use the given URI
    target_uri = URIRef(uri_pattern.replace("(.*)", URI))
    sparql_query = sparql_query.replace("$1", f"<{target_uri}>")

    # get data from the sparql_endpoint, using JSONLD for the graph info
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSONLD)
    result = sparql.query().convert()
    # result.serialize(destination="result.xml", format='xml')

    # transfrom the result data into more usable format.
    # since we have predicates which points towards the target and from the target
    # ( stuff -> p_in -> target -> p_out -> stuff ), we need to distinguish them.
    # TODO function to rewrite URLs

    # returns a sorted list of labels for a given URI or Literal
    def get_labels_for(URI_or_literal):
        return sorted([label for _, label
                       in result.preferredLabel(URI_or_literal, default=[(None, URI_or_literal)])])

    # create quads by predicate, and do a label lookup for each thing on hand
    quads_by_predicate = {}
    for subject_uri, predicate_uri, object, graph in result.quads():
        if subject_uri == target_uri:
            key = (predicate_uri, True)
            value = quads_by_predicate.setdefault(key, {
                "label": get_labels_for(predicate_uri),
                "link": predicate_uri,
                "is_subject": True,
                "objects": []})
            if isinstance(object, URIRef):
                value["objects"].append(
                    {"link": object,
                     "label": get_labels_for(object),
                     "graph": graph.identifier})
            else:
                value["objects"].append(
                    {"link": "",
                     "label": object,
                     "graph": graph.identifier})
        elif object == target_uri:
            key = (predicate_uri, False)
            value = quads_by_predicate.setdefault(key, {
                "label": get_labels_for(predicate_uri),
                "link": predicate_uri,
                "is_subject": False,
                "objects": []})
            value["objects"].append(
                {"link": subject_uri,
                 "label": get_labels_for(subject_uri),
                 "graph": graph.identifier})
        else:
            # otherwise it's a label
            pass

    # sort the predicates and objects so the presentation of the data does not change on a refresh
    sparql_data = sorted(quads_by_predicate.values(),
                         key=lambda item: "".join(item["label"]).casefold())
    for value in sparql_data:
        value["objects"].sort(key=lambda item: "".join(item["label"]).casefold())

    context = {"target_uri": get_labels_for(target_uri)[0]}
    context["sparql_data"] = sparql_data
    print("jvmg", URI, sparql_query, dataset_base, target_uri)
    return render(request, "pubby/page.html", context)


def test(request):
    return HttpResponse("test")
