from django.shortcuts import render, redirect
from pubby.config import getconfig
from SPARQLWrapper import SPARQLWrapper, JSONLD
from rdflib import URIRef, BNode

# Create your views here.


def get_sparql(path, config):
    for ds in config["dataset"]:
        local_path = path.replace(ds["webDataPrefix"], "")
        local_path = local_path.replace(ds["webPagePrefix"], "")
        print(f"Checking Dataset {ds['datasetBase']} for matches.")
        datasetURIPattern = ds["datasetURIPattern"]
        if datasetURIPattern:
            print("Found datasetURIPattern")
            match = datasetURIPattern.fullmatch(ds["datasetBase"].str() + local_path)
            if match:
                print("Matched datasetURIPattern")
                raise NotImplementedError("Not yet implemented")
        useSparqlMapping = ds["useSparqlMapping"]
        if useSparqlMapping:
            uriPattern = useSparqlMapping["uriPattern"]
            match = uriPattern.fullmatch(ds["datasetBase"].str() + local_path)
            if match:
                print("Matched uriPattern")
                sparql = useSparqlMapping["sparqlQuery"]
                for i, group in enumerate(match.groups(), start=1):
                    sparql = sparql.replace(f"${i}", group)
                print("Generated query: " + sparql)
                return sparql



def get(request, URI):
    # get config
    config = getconfig(request)
    sparql_query = config["dataset"][0]["useSparqlMapping"]["sparqlQuery"]
    dataset_base = config["dataset"][0]["datasetBase"]
    sparql_endpoint = str(config["dataset"][0]["sparqlEndpoint"])
    uri_pattern = str(config["dataset"][0]["useSparqlMapping"]["uriPattern"].pattern)
    if sparql_endpoint == "default":
        sparql_endpoint = str(config["defaultEndpoint"])

    # add sparql_query to use the given URI
    resource_uri = URIRef(uri_pattern.replace("(.*)", URI))
    # sparql_query = sparql_query.replace("$1", f"<{resource_uri}>")

    sparql_query = get_sparql(URI, config)
    # print("Query: ", sparql_query)

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
    for subject_uri, predicate_uri, object_uri, graph in result.quads():
        object = None
        is_subject = True
        if subject_uri == resource_uri:
            object = object_uri
        elif object_uri == resource_uri:
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

    context = {"resource_uri": get_labels_for(resource_uri)[0]}
    context["sparql_data"] = sparql_data
    print("jvmg", URI, sparql_query, dataset_base, resource_uri)
    return render(request, "pubby/page.html", context)


def index(request):
    config = getconfig(request)
    print(f"Index, redirecting to {config['indexResource']}")
    return redirect(config["indexResource"].str())

