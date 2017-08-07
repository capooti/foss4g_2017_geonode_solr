# Running asynchronous tasks using the task queues (Celery/RabbitMQ)

## Using signals

Create an utils.py file and copy this python code, readapted from a previous tutorial (file in foss4g_scripts/geonode2solr.py):

```sh
$ touch geonode/solr/utils.py
```

copy this code in utils.py:

```python
import json
import requests


def layer2dict(layer):
    """
    Return a json representation for a GeoNode layer.
    """
    category = ''
    if layer.category:
        category = layer.category.gn_description
    wkt = "ENVELOPE(%s,%s,%s,%s)" % (layer.bbox_x0, layer.bbox_x1, layer.bbox_y1, layer.bbox_y0)
    layer_dict = {
                    'id': str(layer.uuid),
                    'name': layer.name,
                    'title': layer.title,
                    'abstract': layer.abstract,
                    'bbox': wkt,
                    'category': category,
                    'modified_date': layer.date.isoformat()[0:22] + 'Z',
                    'username': layer.owner.username,
                    'keywords': [kw.name for kw in layer.keywords.all()],
                    'regions': [region.name for region in layer.regions.all()],
                }
    print layer_dict
    return layer_dict


def layer_to_solr(layer):
    """
    Sync a layer in Solr.
    """

    layer_dict = layer2dict(layer)

    layer_json = json.dumps(layer_dict)

    url_solr_update = 'http://localhost:8983/solr/boston/update/json/docs'
    headers = {"content-type": "application/json"}
    params = {"commitWithin": 1500}
    res = requests.post(url_solr_update, data=layer_json, params=params,  headers=headers)
    print res.json()
```

Create the signals.py file

```sh
$ /workshop/geonode
$ touch geonode/solr/signals.py
```

Copy this code in signals.py:

```python
from django.db.models.signals import post_save
from geonode.layers.models import Layer
from .utils import layer_to_solr

def sync_solr(sender, instance, created, **kwargs):
    print 'Syncing layer %s with Solr' % instance.typename
    layer_to_solr(instance)

post_save.connect(sync_solr, sender=Layer)
```

Import signals in geonode/solr/__init__.py:

```python
import signals
```



## Test the signal

Now try updating one of the layer, for example:

Then check if in Solr the metadata you updated were correctly synced:

http://localhost:8983/solr/boston/select?indent=on&q=name:%22shape_1%22&wt=json

## Process asynchronously with Celery

Add this at the end of geonode/local_settings.py:

```python
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_ALWAYS_EAGER = False
```

Create this geonode/solr/celery_app.py file:

```python
from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geonode.settings')
app = Celery('geonode')
app.config_from_object('django.conf:settings')
apps = settings.INSTALLED_APPS + ('geonode.solr',)
app.autodiscover_tasks(lambda: apps)
```

Create this geonode/solr/tasks.py file:

```python
from __future__ import absolute_import

from geonode.layers.models import Layer
from celery import shared_task
from .utils import layer_to_solr


@shared_task
def sync_to_solr(layer_id):
    layer = Layer.objects.get(pk=layer_id)
    print 'Syncing layer %s with Solr' % layer.typename
    layer_to_solr(layer)
```

Modify in this wayt the geonode/solr/signals.py file:

```python
from django.db.models.signals import post_save
from geonode.layers.models import Layer
#from .utils import layer_to_solr
from .tasks import sync_to_solr


def sync_solr(sender, instance, created, **kwargs):
    # layer_to_solr(instance)
    sync_to_solr.delay(instance.id)


post_save.connect(sync_solr, sender=Layer)
```

Run Celery in another shell:

```sh
$ . /workshop/env/bin/activate
$ cd /workshop/geonode/geonode
$ celery -A celery_app worker -l info
```

Try saving the metadata of a layer, looking at the Celery log you should see that the Solr task is being executed:

```sh
$ celery -A celery_app worker -l info
 -------------- celery@ubuntu-xenial v3.1.25 (Cipater)
---- **** -----
--- * ***  * -- Linux-4.4.0-89-generic-x86_64-with-Ubuntu-16.04-xenial
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         geonode:0x7f85b2b79bd0
- ** ---------- .> transport:   amqp://guest:**@localhost:5672//
- ** ---------- .> results:     disabled://
- *** --- * --- .> concurrency: 2 (prefork)
-- ******* ----
--- ***** ----- [queues]
 -------------- .> default          exchange=default(direct) key=default


[tasks]
  . geonode.services.tasks.harvest_service_layers
  . geonode.services.tasks.import_service
  . geonode.solr.tasks.sync_to_solr
  . geonode.tasks.deletion.delete_layer
  . geonode.tasks.deletion.delete_map
  . geonode.tasks.deletion.delete_orphaned_document_files
  . geonode.tasks.deletion.delete_orphaned_thumbs
  . geonode.tasks.email.send_email
  . geonode.tasks.email.send_queued_notifications
  . geonode.tasks.update.create_document_thumbnail
  . geonode.tasks.update.geoserver_update_layers

[2017-08-07 16:39:32,161: INFO/MainProcess] Connected to amqp://guest:**@127.0.0.1:5672//
[2017-08-07 16:39:32,174: INFO/MainProcess] mingle: searching for neighbors
[2017-08-07 16:39:33,181: INFO/MainProcess] mingle: all alone
[2017-08-07 16:39:33,194: WARNING/MainProcess] celery@ubuntu-xenial ready.
[2017-08-07 16:40:11,846: INFO/MainProcess] Received task: geonode.solr.tasks.sync_to_solr[6ca1ebbe-4de0-4aec-9fad-0352ca731eb6]
[2017-08-07 16:40:11,910: WARNING/Worker-2] Syncing layer geonode:shape_1 with Solr
[2017-08-07 16:40:11,939: WARNING/Worker-2] {'category': u'Farming', 'modified_date': '2017-07-30T18:02:00Z', 'regions': [u'Hungary', u'Italy'], 'username': u'admin', 'name': u'shape_1', 'title': u'Shape 1 (synced from a celery task )', 'keywords': [u'boston', u'foss4g', u'geonode', u'geoserver', u'gis'], 'abstract': u'synced from signals 2', 'id': '2ebb1de2-757b-11e7-b6ae-02d8e4477a33', 'bbox': 'ENVELOPE(-31.2600000000,34.1000000000,70.0300000000,27.5900000000)'}
[2017-08-07 16:40:11,993: WARNING/Worker-2] {u'responseHeader': {u'status': 0, u'QTime': 13}}
[2017-08-07 16:40:11,994: INFO/MainProcess] Task geonode.solr.tasks.sync_to_solr[6ca1ebbe-4de0-4aec-9fad-0352ca731eb6] succeeded in 0.144630687999s: None
```

## Celery Monitoring

### Using flower

Install and run flower:

```
$ . /workshop/env/bin/activate
$ cd /workshop/geonode/geonode/solr/
$ pip install flower==0.9.2
$ celery flower -A celery_app --port=5555
```

<img src="images/celery/flower_tasks.png" alt="Monitor Celery tasks with Flower" />

To see a failing task one way is to stop Solr

<img src="images/celery/flower_error.png" alt="Monitor a Celery task error with Flower" />
