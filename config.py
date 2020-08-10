from django.conf import settings
from django.urls import resolve
from rdflib import Graph, Namespace, URIRef, BNode
from rdflib.namespace import RDF


CONF = Namespace("http://richard.cyganiak.de/2007/pubby/config.rdf#")

# Cache for the parsed configurations. Contains ConfigElements of the root nodes.
configs = {}

class ConfigElement():
    '''
    Helper Class to allow easy access to configuration values.
    
    Particularly concatenated gets to walk the graph are supported.
    '''
    def __init__(self, graph, subject):
        '''
        The subject represents the starting point in the graph for all accesses to get.
        '''
        self.graph = graph
        self.subject = subject


    def get(self, prop):
        '''
        Returns either a single value or a list.
        If the value(s) are URIRefs or BNodes and therefore potentially subjects
        for further subconfigurations, they are wrapped as ConfigElements.
        '''
        objects = [ConfigElement(self.graph, o) if type(o) in [URIRef, BNode] else o for o in self.graph.objects(self.subject, CONF[prop])]
        if len(objects)==0:
            return None
        elif len(objects)==1:
            return objects[0]
        else:
            return objects


    def value(self):
        '''
        Returns the wrapped subject, either a URIRef or a BNode.
        '''
        return self.subject


    def __repr__(self):
        return str(self.subject)




def getconfig(request):
    '''
    Gets access to the root ConfigElement. 
    The namespace is determined based on the request path.
    '''
    namespace = resolve(request.path).namespace
    return configs[namespace]


def init_config():
    '''
    During startup, all configured Pubby configurations are parsed and
    prepared as ConfigElements.
    '''
    conf_setting = settings.PUBBY_CONFIG
    # Special case if we only have one instance and one config
    if type(conf_setting) == str:
        conf_setting = { "pubby": conf_setting }
    for namespace, file_path in conf_setting.items():
        g = Graph()
        with open(file_path, "r", encoding="utf-8") as f:
            g.parse(f, format="turtle")
        subject = g.value(None, RDF.type, CONF.Configuration, any=False)
        configs[namespace] = ConfigElement(g, subject)
        print(f"Pubby configured for namespace '{namespace}', using '{file_path}'")


