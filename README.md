# Pubby (Django-Version)

This is a reimplementation of [Pubby](http://wifo5-03.informatik.uni-mannheim.de/pubby/) in Python/Django.

You maybe need to install the RDFLib JSON-LD plugin first:

pip install rdflib-jsonld

## Getting started

Per default, the [JudaicaLink](http://web.judaicalink.org/) endpoint is configured. Start the Django server as usual and go to http://localhost:8002/pubby to browse the data.

The pubby instances are configured in server/settings.py.

The default instance configuration is at pubby/config.ttl 

## Installation

For installation on the server you can add a webhook. See [here](https://github.com/FlorianRupp/django-webhook-consume.git).
Make sure you have git installed.
