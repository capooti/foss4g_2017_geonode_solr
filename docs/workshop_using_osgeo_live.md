# Things to change from the FOSS4G 2017 GeoNode workshop to use OSGeo Live

## Django

Change permissions on this directory:

```sh
sudo chmod -R 777 /var/www/geonode/uploaded
```

Settings file: /usr/lib/python2.7/dist-packages/geonode/local_settings.py

To run the shell:

```sh
export DJANGO_SETTINGS_MODULE=geonode.settings
django-admin shell
```

## PostgreSQL

Django app
* database: geonode_app
* user: user
* password: user

Uploads
* database: geonode_data
* user: user
* password: user

## GeoServer

Running on port 8082: http://localhost:8082/geoserver

## GeoWebCache

In Caching Defaults set the “Enable direct integration with GeoServer WMS”

## pycsw

Running at: http://geonode/pycsw
