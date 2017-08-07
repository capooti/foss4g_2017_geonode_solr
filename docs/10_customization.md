# Developing a custom application for GeoNode

## Create the application

Activate the virtualenv:

```sh
$ . /workshop/env/bin/activate
$ cd /workshop/geonode/geonode/
$ python manage.py startapp solr
```

Create the template:

```sh
$ mkdir -p geonode/sol/templates/solr
$ touch geonode/solr/templates/solr/index.html
```

Add this html code in the index.html template:

```html
{% extends "site_base.html" %}
{% load i18n %}
{% load url from future %}

{% block title %} {{ block.super }} {% endblock %}
{% block body_class %}people{% endblock %}
{% block body_outer %}

{% block body %}

    <h3>Search Metadata</h3>
    <form type="GET" action="." style="margin: 0">
        <input  id="search_text" type="text" name="search_text"  placeholder="Search..." >
        <button id="search_submit" type="submit" >Submit</button>
    </form>

    <p>Displaying 10 of {{ count }} results</p>

    {% for document in docs %}
    <h4>{{ document.title }}</h4>
    <ul>
        <li>Score: {{ document.score }}</li>
        <li>Abstract: {{ document.abstract | truncatechars:200 }}
        <li>Category: {{ document.category }}</li>
        <li>Date: {{ document.modified_date.0 }}</li>
        <li>Regions:</li>
            <ul>
            {% for region in document.regions %}
                <li>{{ region }}</li>
            {% endfor %}
            </ul>
        <li>Keywords:</li>
            <ul>
            {% for keyword in document.keywords %}
                <li>{{ keyword }}</li>
            {% endfor %}
            </ul>
    </ul>
    {% endfor %}

{% endblock body %}

{% block sidebar %}{% endblock sidebar %}
{% endblock body_outer %}
```

## Create the url dispatchers

Add this code at the end of geonode/urls.py

```python
# search custom application urls
urlpatterns += patterns('',
    url(r'^solr/', include('geonode.solr.urls')),
)
```

```sh
$ touch geonode/solr/urls.py
```

Add this code in urls.py:

```python
from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.solr.views',
                       url(r'^$', 'index', name='index'),
                       )
```

## Add the application in local_settings

```python
from django.conf import settings
settings.INSTALLED_APPS = settings.INSTALLED_APPS + ('geonode.solr',)
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))
settings.TEMPLATES[0]['DIRS'].insert(0, os.path.join(LOCAL_ROOT, "solr/templates"))
```

## Create the view

Add this code to create the view in geonode/solr/views.py:

```python
import json, requests
from django.shortcuts import render_to_response
from django.template import RequestContext


def index(request):
    '''
    A view to search metadata in Solr.
    '''

    search_text = '*'
    if request.method == 'GET':
            if 'search_text' in request.GET:
                search_text = request.GET.get('search_text', None)
    if not search_text:
        search_text = '*'

    url = 'http://localhost:8983/solr/boston/select'
    params = dict(
        q='_text_:%s' % search_text,
        fl='*,score',
        wt='json'
    )
    resp = requests.get(url=url, params=params)
    data = json.loads(resp.text)

    count = data['response']['numFound']
    docs = data['response']['docs']
    return render_to_response('solr/index.html',
                                RequestContext(request,
                                    {
                                        'docs': docs,
                                        'count': count,
                                    },
                                )
                            )
```

## Visit the new page

http://localhost:8000/solr/

<img src="images/customization/custom_geonode_app.png" alt="Custom GeoNode application" />

## Bonus step

* Implements pagination
