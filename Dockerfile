FROM python:3.8-slim

RUN mkdir /app
COPY server /app
WORKDIR /app

EXPOSE 8000

RUN pip install SPARQLWrapper rdflib django regex rdflib-jsonld

CMD python manage.py runserver 0.0.0.0:8000

# docker build -t  pubby .
# docker run --publish 8000:8000 pubby

# Problem: redirects to port 8000 when running on port 80.