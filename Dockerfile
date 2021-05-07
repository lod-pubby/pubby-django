FROM python:3.8-slim

RUN mkdir /app
COPY server /app
WORKDIR /app

EXPOSE 80

RUN pip install SPARQLWrapper rdflib django regex

CMD python manage.py runserver 0.0.0.0:80