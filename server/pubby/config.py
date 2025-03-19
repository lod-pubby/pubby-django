import logging

from django.conf import settings
from django.urls import resolve
from rdflib import Graph, Namespace, URIRef, BNode
from rdflib.namespace import RDF
import re

logger = logging.getLogger(__name__)

CONF = Namespace("http://richard.cyganiak.de/2007/pubby/config.rdf#")
FUNCTIONAL = [
    CONF.projectName,
    CONF.projectHomepage,
    CONF.webBase,
    CONF.defaultLanguage,
    CONF.indexResource,
    CONF.showLabels,
    CONF.defaultEndpoint,
    CONF.sparqlEndpoint,
    CONF.datasetBase,
    CONF.datasetURIPattern,
    CONF.priority,
    CONF.addSameAsStatements,
    CONF.webResourcePrefix,
    CONF.webDataPrefix,
    CONF.webPagePrefix,
    CONF.useSparqlMapping,
    CONF.uriPattern,
    CONF.sparqlQuery,
    CONF.primaryResource,
    CONF.fixUnescapedCharacters,
    CONF.metadataTemplate,
]

PATTERN = [
    CONF.datasetURIPattern,
    CONF.uriPattern
]

# Cache for the parsed configurations. Contains ConfigElements of the root nodes.
configs = {}


class ConfigElement():
    """
    Helper Class to allow easy access to configuration values.

    Particularly concatenated gets to walk the graph are supported.
    """

    def __init__(self, graph, subject):
        """
        The subject represents the starting point in the graph for all accesses to get.
        """
        self.graph = graph
        self.subject = subject
        self.cache = {}

    def get(self, prop):
        """
        Returns either a single value or a list.

        If the value(s) are URIRefs or BNodes and therefore potentially subjects
        for further subconfigurations, they are wrapped as ConfigElements.

        If the property is a known property for patterns, a regex is compiled
        and returned.
        """
        if prop in self.cache:
            return self.cache[prop]
        objects = self.graph.objects(self.subject, CONF[prop])
        res = [ConfigElement(self.graph, o) if type(o) in [URIRef, BNode] else o.toPython() for o in objects]
        if CONF[prop] in PATTERN and len(res) == 1:
            regex = re.compile(res[0])
            self.cache[prop] = regex
            return regex
        elif CONF[prop] in FUNCTIONAL and len(res) == 0:
            self.cache[prop] = None
            return None
        elif CONF[prop] in FUNCTIONAL and len(res) == 1:
            self.cache[prop] = res[0]
            return res[0]
        else:
            self.cache[prop] = res
            return res

    def __getitem__(self, prop):
        """
        Configuration can be accessed like this: config['projectName']
        """
        return self.get(prop)

    def value(self):
        """
        Returns the wrapped subject, either a URIRef or a BNode.
        """
        return self.subject

    def str(self):
        """
        Returns the wrapped subject as String.
        """
        return str(self.subject)

    def shorten(self, uri):
        """
        Decomposes a URL with respect to the configured namespaces.

        Example:
        g.compute_qname(URIRef(“http://foo/bar#baz”)) returns
        (“ns2”, URIRef(“http://foo/bar#”), “baz”))
        """
        if type(uri) == str:
            uri = URIRef(uri)
        try:
            res = self.graph.compute_qname(str(uri), generate=False)
        except Exception as e:
            res = (None, None, str(uri))
        return res

    def __repr__(self):
        return str(self.subject)


def getconfig(request):
    """
    Gets access to the root ConfigElement.
    The namespace is determined based on the request path.
    """
    logger.debug("request.path:", request.path)
    print("request.path:", request.path)
    namespace = resolve(request.path).namespace
    logger.debug("namespace:", namespace)
    print("namespace:", namespace)
    return configs[namespace]


def init_config():
    """
    During startup, all configured Pubby configurations are parsed and
    prepared as ConfigElements.
    """
    conf_setting = settings.PUBBY_CONFIG
    # Special case if we only have one instance and one config
    if type(conf_setting) == str:
        conf_setting = {"pubby": conf_setting}
    for namespace, file_path in conf_setting.items():
        g = Graph()
        with open(file_path, "r", encoding="utf-8") as f:
            g.parse(f, format="turtle")
            for ns in g.namespaces():
                logger.debug("Namespaces configured :%s", ns)
        subject = g.value(None, RDF.type, CONF.Configuration, any=False)
        configs[namespace] = ConfigElement(g, subject)
        logger.debug("Pubby configured for namespace '%s', using '%d'", namespace, file_path)
