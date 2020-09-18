from django.shortcuts import render, redirect
from pubby.config import getconfig
from SPARQLWrapper import SPARQLWrapper, JSONLD
from rdflib import URIRef, BNode

# Create your views here.

class Resource:
    def __init__(self, request, request_path):
        self.config = getconfig(request)
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
                match = uriPattern.fullmatch(self.resource_uri)
                if match:
                    print("Matched uriPattern")
                    sparql = useSparqlMapping["sparqlQuery"]
                    for i, group in enumerate(match.groups(), start=1):
                        sparql = sparql.replace(f"${i}", group)
                    print("Generated query: " + sparql)
                    self.sparql_query = sparql
                    return
        raise ValueError(f"No matching Dataset in configuration for {request_path}")


def get(request, URI):
    
    resource = Resource(request, URI)

    # print("Query: ", sparql_query)

    # get data from the sparql_endpoint, using JSONLD for the graph info
    sparql = SPARQLWrapper(resource.sparql_endpoint)
    sparql.setQuery(resource.sparql_query)
    sparql.setReturnFormat(JSONLD)
    result = sparql.query().convert()
    # print(f"Result {result.serialize()}")
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
            "label": get_labels_for(predicate_uri),
            "link": predicate_uri,
            "is_subject": is_subject,
            "objects": [],
            "graph": {"link": graph.identifier if not isinstance(graph.identifier, BNode) else "",
                      "label": graph.identifier.split("/")[-1]
                      }
        })
        if isinstance(object, URIRef):
            value["objects"].append(
                {"link": object,
                 "label": get_labels_for(object)})
        else:
            value["objects"].append(
                {"link": "",
                 "label": object})

    # sort the predicates and objects so the presentation of the data does not change on a refresh
    sparql_data = sorted(quads_by_predicate.values(),
                         key=lambda item: "".join(item["label"]).casefold())
    for value in sparql_data:
        value["objects"].sort(key=lambda item: "".join(item["label"]).casefold())
        value["num_objects"] = len(value["objects"])

    context = {"resource_uri": get_labels_for(resource.resource_uri)[0]}
    context["sparql_data"] = sparql_data

    return render(request, "pubby/page.html", context)


def index(request):
    config = getconfig(request)
    print(f"Index, redirecting to {config['indexResource']}")
    return redirect(config["indexResource"].str())

