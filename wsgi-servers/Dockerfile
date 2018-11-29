FROM python:alpine3.7

LABEL version="1.0" maintainer="Jean Metz"

RUN apk update && apk add \
    build-base \
    libev-dev \
    python-dev 
    

# due to problems with libraries uwsgi uses ...
# https://stackoverflow.com/questions/36217250/cannot-install-uwsgi-on-alpine#36854461
# https://github.com/gliderlabs/docker-alpine/issues/158
RUN apk add \
    linux-headers \
    pcre-dev

# Install the WSGI servers 
RUN pip install \
    bjoern \
    cherrypy \
    gunicorn \
    meinheld \
    tornado \
    uwsgi \
    waitress   

RUN mkdir -p /home/wsgi_benchmark/www

COPY src /home/wsgi_benchmark/www
WORKDIR /home/wsgi_benchmark/www