# Running asynchronous tasks using a task queue (Celery/RabbitMQ)

The HTTP request/response cycle can be kept synchronous as far as there are very quick interactions (few milliseconds) between the client and the servers.

Unfortunately there are cases when the cycle become slower and slower because of some time consuming tasks (1, 2 seconds or even more...): in these situations the best practice for a web application is to process asynchronously these tasks using a task queue.

Furthermore some task must be scheduled, or need to interact with external services, which can take time.
In those cases we run these longer tasks separately, in different processes.

<img src="images/celery/sync_vs_async.png" alt="Sync vs Async processing" />

## Task queues

Typical uses cases in a web application where a task queue is the way to go:

* Asynchronous tasks such as:
  * Thumbnails generation
  * Notifications
  * Data denormalization
  * Search index synchronization
* Replacing cron jobs
  * Backups
  * Maintenance jobs
  * pdf reports

In the case of a geoportal platform as GeoNode the use cases can be extended to:

* Upload a shapefile to the server (next generation GeoNode)
* OGC services harvesting (Harvard Hypermap)
* GeoProcessing operations
* Geodata maintenance

### Asynchronous processing model

The asynchronous processing model is composed by services that create processing tasks and by services which consume and process these tasks accordingly.

A **message queue** is a **broker** which facilitates message passing by providing a protocol or interface which other services can access. In the context of a web application as GeoNode the **producer** is the client application that creates messages based on the user interaction (for example a user that saves metadata, and sends a synchronization process to the search engine). The **consumer** is a daemon process (**Celery** in the case of GeoNode) that can consume the messages and run the needed process.

A more complex use case is when there are two or more applications which are the producer and consumer of the messages. For example the user of the web application, written in Django, could produce a message which is consumed by a daemon of an another program.

<img src="images/celery/async_model.png" alt="Async processing model" />

### Celery and RabbitMQ

[Celery](http://www.celeryproject.org/) is the default task queue for GeoNode. It provides:

* asynchronous task queue/job queue based on distributed message passing
* focused on real-time operation, but supports scheduling as well
* the execution units, called tasks, are executed concurrently on a single or more worker servers
* it supports many message brokers (RabbitMQ, Redis, MongoDB, CouchDB, ...)
* written in Python but it can operate with other languages
* great integration with Django (it was born as a Django application)
* great monitoring tools (Flower, django-celery-results)

[RabbitMQ](https://www.rabbitmq.com) is the messabe broker which comes by default with GeoNode (it is possible to replace it with something different like Redis):

* as a message broker: it accepts and forwards messages
* it is by far the most widely deployed open source broker (35k+ deployments)
* support many message protocols
* supported by many operating systems and languages

<img src="images/celery/architecture.png" alt="Celery and RabbitMQ architecture" />

## Using Celery in your application

In this tutorial you will improve the application developed in the previous tutorial. Previously you had a script which was syncing all of the GeoNode layers metadata to Solr (*foss4g_scripts/geonode2solr*). Instead than running this script periodically for all of the layers, a better approach would be to syncronize in Solr a layer as soon as the metadata for that layer are saved in GeoNode by the user.

As the metadata Solr synchronization process can slow down the user interaction with the application, you will send that process asynchronously using Celery and RabbitMQ. You will see how you can use Celery to reliably process these tasks, and how to use the [Flower Celering monitoring tool](http://flower.readthedocs.io/) to analyze the processed tasks.

## Using Django signals

You need a way to run the synchronization process to Solr from GeoNode as soon as the user save the metadata for a given layer.

One way to accomplish this is by forking the GeoNode metadata update view. But forking is the wrong way to do things as it introduces a lot of complications when updating to a newer GeoNode version.

So, how can you execute the sync process without forking GeoNode? [Django signals](https://docs.djangoproject.com/en/1.11/topics/signals/) provides a convenient way to do this.

> Django includes a “signal dispatcher” which helps allow decoupled applications get notified when actions occur elsewhere in the framework. In a nutshell, signals allow certain senders to notify a set of receivers that some action has taken place. They’re especially useful when many pieces of code may be interested in the same events.

Django provides a set of built-in signals that let user code get notified by Django itself of certain actions. These include some useful notifications like for example the notification that happens when saving an instance.

You will use the post_save signal which is run when a GeoNode layer is saved to run the Solr synchronization code.

For this purpose, create an *geonode/solr/utils.py* file and copy this python code, readapted from a previous tutorial (check the *foss4g_scripts/geonode2solr.py* file):

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

Now, create the *geonode/solr/signals.py* file and add this code in it:

```python
from django.db.models.signals import post_save
from geonode.layers.models import Layer
from .utils import layer_to_solr

def sync_solr(sender, instance, created, **kwargs):
    print 'Syncing layer %s with Solr' % instance.typename
    layer_to_solr(instance)

post_save.connect(sync_solr, sender=Layer)
```

Thanks to the post_save signal, sync_solr will be run every time a layer is saved.

Finally import signals in *geonode/solr/__init__.py*:

```python
import signals
```

## Test the signal

Now to test the layer post_save signal you just created, try updating one of the layer (for this purpose, go the layer page, then click on *Edit Layer* then on *Edit Metadata*)

Change some of the metadata and then check if in Solr the metadata you updated were correctly synced:

http://localhost:8983/solr/boston/select?indent=on&q=name:%22biketrails_arc_p%22&wt=json

(you need to change the q=name parameter to your layer's name)

## Process asynchronously with Celery

Now you found a great way to run the *layer_to_solr* method without forking GeoNode, but you are still doing a synchronous processing. Let's add Celery and RabbitMQ to the mix!

Add this at the end of *geonode/local_settings.py*:

```python
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_ALWAYS_EAGER = False
```

*BROKER_URL* is the location where RabbitMQ is running. You will send the tasks as the *guest* user. In production it is recommendable to create a specific user with a strong password.

Now create this *geonode/solr/celery_app.py* file, which will make your custom task discoverable by Celery:

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

Create this *geonode/solr/tasks.py* file which contain the Celery task (the **consumer**, in the jargon, while the post_save signal is the **producer**):

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

Now modify in this way the *geonode/solr/signals.py* file:

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

Let's see if everything works. Run the Celery worker by opening another shell (in production you should consider using a tool such as [supervisord](http://supervisord.org/)):

```sh
$ . /workshop/env/bin/activate
$ cd /workshop/geonode/geonode/solr
$ celery -A celery_app worker -l info
```

Try saving the metadata of a layer. Looking at the Celery log you should see that the Solr task is being executed:

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
[2017-08-07 16:40:11,939: WARNING/Worker-2] {'category': u'Farming', 'modified_date': '2017-07-30T18:02:00Z', 'regions': [u'Hungary', u'France'], 'username': u'admin', 'name': u'shape_1', 'title': u'Shape 1 (synced from a celery task )', 'keywords': [u'boston', u'foss4g', u'geonode', u'geoserver', u'gis'], 'abstract': u'synced from signals 2', 'id': '2ebb1de2-757b-11e7-b6ae-02d8e4477a33', 'bbox': 'ENVELOPE(-31.2600000000,34.1000000000,70.0300000000,27.5900000000)'}
[2017-08-07 16:40:11,993: WARNING/Worker-2] {u'responseHeader': {u'status': 0, u'QTime': 13}}
[2017-08-07 16:40:11,994: INFO/MainProcess] Task geonode.solr.tasks.sync_to_solr[6ca1ebbe-4de0-4aec-9fad-0352ca731eb6] succeeded in 0.144630687999s: None
```

## Celery Monitoring

A great Celery monitoring tool is Flower.

Install and run Flower at port 5555:

```
$ . /workshop/env/bin/activate
$ cd /workshop/geonode/geonode/solr/
$ pip install flower==0.9.2
$ celery flower -A celery_app --port=5555
```

Now browse at http://localhost:5555 and you should see the Flower main interface. Try saving some of the layers, and you should see a new task for each layer you save in Flower.

<img src="images/celery/flower_tasks.png" alt="Monitor Celery tasks with Flower" />

If you want to see a failing task, as in the previous image, one way is to stop Solr and then saving a layer. You can see details of the error which made the task failing by clicking on the failing task itself in the Flower interface

<img src="images/celery/flower_error.png" alt="Monitor a Celery task error with Flower" />
