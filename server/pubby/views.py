from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from pubby.config import getconfig
from SPARQLWrapper import SPARQLWrapper, JSONLD
from rdflib import URIRef, BNode, Literal
from urllib.parse import unquote
import regex as re
from .gnd import fetch_gnd_id
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
        # primary resource
        self.primary_resource = ""
        # publish resources
        self.publish_resources = []

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
                    primary_resource = useSparqlMapping["primaryResource"]
                    publish_resources = useSparqlMapping["publishResources"]
                    for i, group in enumerate(match.groups(), start=1):
                        sparql = sparql.replace(f"${i}", group)
                        primary_resource = primary_resource.replace(f"${i}", group)
                        publish_resources = [resource.replace(f"${i}", group) for resource in publish_resources ]
                    self.sparql_query = sparql
                    self.primary_resource = URIRef(primary_resource)
                    self.publish_resources = [URIRef(resource) for resource in publish_resources]
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

    accept = request.META.get("HTTP_ACCEPT").lower()
    serialization = "html"
    # Not a real content negotiation, simply the first match
    # in our dictionary is used.
    for mime in mime2serialisation:
        if mime in accept:
            serialization = mime2serialisation[mime]
            break
    print(accept)
    print(f"Content negotiation: {serialization}")

    # Only redirect if we are at the resource URI, not at the html or rdf views
    if resource.resource_path == resource.request_path:
        if serialization == "html":
            return HttpResponseSeeOther(resource.web_base + resource.page_path)
        else:
            return HttpResponseSeeOther(resource.web_base + resource.data_path)


    # get data from the sparql_endpoint, using JSONLD for the graph info
    sparql = SPARQLWrapper(resource.sparql_endpoint)
    sparql.setQuery(resource.sparql_query)
    # We need JSON-LD to get the graph information
    sparql.setReturnFormat(JSONLD)
    result = sparql.query().convert()

    # We want data
    if resource.request_path == resource.data_path:
        # Hard-coded decision what we deliver if a browser accesses our data page
        if serialization == "html":
            serialization = "turtle"
            mime = "text/turtle"
        response = HttpResponse()
        response.content = result.serialize(format=serialization)
        response.content_type = f"{mime};charset=utf-8"
        return response


    primary_resource = create_quad_by_predicate(resource.primary_resource, resource, result)
    publish_resources = []
    for publish_resource in resource.publish_resources:
        publish_resources.append(create_quad_by_predicate(publish_resource, resource, result))

    context = {"resource_label": get_labels_for(resource.resource_uri, result, resource)[0]["label_or_uri"]}
    # What is in primary_resource
    context["primary_resource"] = primary_resource
    context["publish_resources"] = publish_resources
    context["resource_uri"] = resource.resource_uri
    context["gndid"] = fetch_gnd_id(resource.resource_uri)
    return render(request, "pubby/page.html", context)


def create_quad_by_predicate(uri, resource, result):
    # create quads by predicate, and do a label lookup for each thing on hand
    quads_by_predicate = {}
    for subject_uri, predicate_uri, object_uri, graph in result.quads():
        object = None
        is_subject = True
        if subject_uri == uri:
            object = object_uri
        elif object_uri == uri:
            is_subject = False
            object = subject_uri
        else:
            # otherwise it's a label
            continue

        key = (predicate_uri, is_subject, graph.identifier)
        value = quads_by_predicate.setdefault(key, {
            "labels": get_labels_for(predicate_uri, result, resource),
            "link": rewrite_URL(predicate_uri, resource.dataset_base, resource.web_base),
            "qname": resource.config.shorten(predicate_uri),
            "is_subject": is_subject,
            "objects": [],
            "graph": {"link": rewrite_URL(graph.identifier, resource.dataset_base, resource.web_base) if not isinstance(graph.identifier, BNode) else None,
                      "label": graph.identifier.split("/")[-1]
                      }
        })
        if isinstance(object, URIRef):
            value["objects"].append(
                {"link": rewrite_URL(object, resource.dataset_base, resource.web_base),
                 "qname": resource.config.shorten(predicate_uri),
                 "labels": get_labels_for(object, result, resource)})
        else:
            value["objects"].append(
                {"link": None,
                 "qname": None,
                 "labels": get_labels_for(object, result, resource)})

    # sort the predicates and objects so the presentation of the data does not change on a refresh
    sparql_data = sorted(quads_by_predicate.values(),
                         key=lambda item: item["labels"][0]["label_or_uri"])
    for value in sparql_data:
        value["objects"].sort(key=lambda item: item["labels"][0]["label_or_uri"])
        value["num_objects"] = len(value["objects"])

    return sparql_data


uri_spaces = re.compile(r"[-_+.#?]")
camel_case_words = re.compile(r"[\p{L}\p{N}][^\p{Lu} ]*")
bad_chars = "?="
bad_words = ["html", "xml", "ttl"]


def calculate_heuristic_label(uri):
        uri = unquote(uri)
        elements = uri.split("/")
        elements.reverse()
        for element in elements:
            if element != '':
                last_element = element
                break
        last_element = uri_spaces.sub(" ", last_element)
        words = last_element.split(" ")
        filtered_words = filter(lambda word: word not in bad_words, words)
        filtered_words = filter(lambda word: all(char not in bad_chars for char in word),
                                filtered_words)
        filtered_words = " ".join(list(filtered_words))
        last_element = " ".join(camel_case_words.findall(filtered_words))
        " ".join([word.capitalize() for word in last_element.split(" ")])
        return " ".join([word.capitalize() for word in last_element.split(" ")])


# transfrom the result data into more usable format.
# since we have predicates which points towards the target and from the target
# ( stuff -> p_in -> target -> p_out -> stuff ), we need to distinguish them.

# returns a sorted list of labels for a given URI or Literal
def get_labels_for(URI_or_literal, result, resource):
    '''
    Each predicate and each value (subject or object) can have multiple labels.
    To support various options how to present the information in the template,
    a list of dictionaries is created:
    [
        {
            "label": A label as rdflib Literal, if it exists, otherwise none.
            "label_or_uri": label or local name from qname, used for sorting.
            "uri": the full qualified URI of the resource as string.
            "qname": The deconstructed URI using configured namespaces, see ConfigElement#shorten()
            "heuristic": A calculated version for a label based on the URI.
        }
    ]
    '''
    labels = []
    for _, label in result.preferredLabel(URI_or_literal, default=[(None, URI_or_literal)]):
        label_dict = {}
        if isinstance(label, URIRef):
            label_dict["label"] = None
            label_dict["uri"] = str(URI_or_literal)
            label_dict["qname"] = resource.config.shorten(URI_or_literal)
            label_dict["heuristic"] = calculate_heuristic_label(label_dict["uri"])
            label_dict["label_or_uri"] = label_dict["uri"]
        else:
            label_dict["label"] = label
            label_dict["uri"] = None
            label_dict["qname"] = None
            label_dict["heuristic"] = None
            label_dict["label_or_uri"] = label_dict["label"]
        labels.append(label_dict)
    return sorted(labels, key=lambda label: label["label_or_uri"])


def index(request):
    config = getconfig(request)
    print(f"Index, redirecting to {config['indexResource']}")
    return redirect(config["indexResource"].str())

