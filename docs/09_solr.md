# Using a search engine with GeoNode: a quick tour of Solr

> Solr is an open source enterprise search platform, written in Java, from the Apache Lucene project. Its major features include full-text search, hit highlighting, faceted search, real-time indexing, dynamic clustering, database integration, NoSQL features and rich document (e.g., Word, PDF) handling. Providing distributed search and index replication, Solr is designed for scalability and fault tolerance. Solr is the second-most popular enterprise search engine after Elasticsearch.

> Solr runs as a standalone full-text search server. It uses the Lucene Java search library at its core for full-text indexing and search, and has REST-like HTTP/XML and JSON APIs that make it usable from most popular programming languages. Solr's external configuration allows it to be tailored to many types of application without Java coding, and it has a plugin architecture to support more advanced customization.

> Apache Lucene and Apache Solr are both produced by the same Apache Software Foundation development team since the two projects were merged in 2010. It is common to refer to the technology or products as Lucene/Solr or Solr/Lucene.

As CMS are adding Solr (or Elasticsearch) to the stack to improve user search experience, Solr can be very useful in the context of an SDI as it provides features which are not traditionally provided by GeoPortals and OGC standards.

In this tutorial you will get an understanding about how to use Solr together with GeoNode to provide to end users a better search experience with features such as:

* full text metadata search
* scored results
* proximity matching text search
* boosts
* date ranges metadata search
* keyword, temporal and spatial faceting
* Solr spatial features

If you are willing to improve your understanding of Solr some very useful resources are:

* [Solr quick start](http://lucene.apache.org/solr/quickstart.html)
* [Apache Solr Reference Guide](http://lucene.apache.org/solr/guide/)
* [Apache Solr Enterprise Search Server](https://www.packtpub.com/big-data-and-business-intelligence/apache-solr-enterprise-search-server-third-edition) by David Smiley

## Create a core

Solr is running at http://localhost:8983/solr

As a first thing create a core for the aims of this tutorial. You will name the core *boston*

```sh
$ sudo su solr
$ cd /opt/solr-6.6.0/bin/
$ ./solr create -c boston
```

Now check if the new core is available from the Solr admin interface, which is running at: http://localhost:8983/solr/#/

You should be able to see *boston* in the *core selector* select list

<img src="images/solr/new_core.png" alt="Solr new core" />

In case you need to restart from scratch, here is how to remove the core:

```sh
$ sudo su solr
$ cd /opt/solr-6.6.0/bin/
$ ./solr delete -c boston
```

## Create a schema

Solr stores details about the field types and fields it is expected to understand in a schema file. The name and location of this file may vary depending on how you initially configured Solr or if you modified it later.

managed-schema is the name for the schema file Solr uses by default to support making Schema changes at runtime via the Schema API, or Schemaless Mode features.

You will create the schema for the *boston* core by sending POST JSON requests to the Solr API (http://localhost:8983/solr/boston/schema endpoint) with Python and the great [Requests Python library](http://docs.python-requests.org/en/master/)

Create a directory where you will add the Python script, a __init__.py file into it and then the Python script itself (named *solr_schema*):

```sh
$ mkdir /workshop/foss4g_scripts
$ touch /workshop/foss4g_scripts/__init__.py
$ touch /workshop/foss4g_scripts/solr_schema.py
```

The __init__.py files is required to make Python treat the directory as containing packages. This way you will be able to import the solr_schema package in the Django shell.

Add the following Python code to the *solr_schema.py* script:

```python
import requests


schema_url = "http://localhost:8983/solr/boston/schema"


def create_schema():
    """
    Create the schema in the solr core.
    """

    # create a special type to draw better heatmaps
    location_rpt_quad_5m_payload = {
        "add-field-type": {
            "name": "location_rpt_quad_5m",
            "class": "solr.SpatialRecursivePrefixTreeFieldType",
            "geo": False,
            "worldBounds": "ENVELOPE(-180, 180, 180, -180)",
            "prefixTree": "packedQuad",
            "distErrPct": "0.025",
            "maxDistErr": "0.001",
            "distanceUnits": "degrees"
        }
    }
    requests.post(schema_url, json=location_rpt_quad_5m_payload)

    # create the DateRangeField type
    date_range_field_type_payload = {
        "add-field-type": {
            "name": "rdates",
            "class": "solr.DateRangeField",
            "multiValued": True
        }
    }
    requests.post(schema_url, json=date_range_field_type_payload)

    # now the other fields. The types are common and they are added by default to the Solr schema
    fields = [
        {"name": "name", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "abstract", "type": "string"},
        {"name": "bbox", "type": "location_rpt_quad_5m"},
        {"name": "category", "type": "string"},
        {"name": "modified_date", "type": "rdates"},
        {"name": "username", "type": "string"},
        {"name": "keywords", "type": "string", "multiValued": True},
        {"name": "regions", "type": "string", "multiValued": True},
    ]

    headers = {
        "Content-type": "application/json"
    }

    for field in fields:
        data = {
            "add-field": field
        }
        requests.post(schema_url, json=data, headers=headers)

    print 'Schema generated.'
```

Now run the script using the Django shell. Before of that create a symbolic link to the foss4g_scripts directory:

```sh
$ cd /workshop/geonode/
ln -s ../foss4g_scripts .
$ python manage.py shell
>>> from foss4g_scripts import solr_schema
>>> solr_schema.create_schema()
```

Make sure the schema was generated by checking the schema endpoint at the Solr administrative site

<img src="images/solr/schema_generated.png" alt="Solr new core" />

## Indexing data

The way you can pair Solr to GeoNode is by keeping in sync the GeoNode metadata for each layer, which are contained in a relational structure, to the Solr denormalized structure, based on documents. You will keep in sync the single metadata record for a given layer to the Solr document for that layer. In this tutorial you will keep in sync only some of the metadata, but once you master the concept the possibilities are limitless.

There is a number of way to load (index) data in Solr. Here you will use Python and the great [Requests Python library](http://docs.python-requests.org/en/master/) to send POST JSON request to the Solr endpoint in order to create and update documents.

Create the Python script:

```sh
$ touch touch /workshop/foss4g_scripts/geonode2solr.py
```

Now add this Python code in geonode2solr.py:

```python
import json
import requests
from geonode.layers.models import Layer


def layer2dict(layer):
    """
    Return a json representation for a GeoNode layer.
    """
    category = ''
    if layer.category:
        category = layer.category.gn_description
    wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(layer.bbox_x0, layer.bbox_x1, layer.bbox_y1, layer.bbox_y0)
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


def sync():
    """
    Sync GeoNode layers with Solr.
    """
    for layer in Layer.objects.all():
        print 'Syncing layer %s to Solr' % layer.name
        layer_to_solr(layer)
```

Now run the script using the Django shell:

```sh
$ cd /workshop/geonode/
$ python manage.py shell
>>> from foss4g_scripts import geonode2solr
>>> geonode2solr.sync()
```

Check if data were added to Solr by checking this endpoint (more on this later): http://localhost:8983/solr/boston/select?indent=on&q=*:*&wt=json

## Indexing more data

A search engine is really useful when there are hundreds if not thousands of records to search. Your workshop GeoNode instance right now contains not even 10 layers (metadata records). Therefore for the aim of the tutorial you need a more extended instance with at least some hundreds of metadata.

For this purpose you will harvest metadata for a very large CSW catalogue, and will index these metadata in Solr. The catalogue you are going to use for this purpose is [Harvard Hyperamp](http://hh.worldmap.harvard.edu/), which right now contains almost 200,000 layers metadata records. In case you are interested in Harvard Hypermap code base, you can check it out the [CGA Harvard Hypermap github repository](https://github.com/cga-harvard/HHypermap)

You will harvest not all of the HHypermap layers, but just a part of them.

To make things more heterogeneous you will:

* add to each layer's metadata a random category (from the ones in GeoNode)
* use for each layer's metadata a random date (from 01-01-1970 to 12-01-2016)
* add to each layer's metadata up to 5 different regions (from the ones in GeoNode)
* add to each layer's metadata up to 5 different keywords (from an hard coded list)

Feel free to modify the script a you wish.

Create a Python script named *csw2solr.py*:

```sh
$ touch touch /workshop/foss4g_scripts/csw2solr.py
```

Add this Python code in the csw2solr script:

```python
import json
import requests
import datetime
from random import randint
from owslib.csw import CatalogueServiceWeb
from geonode.base.models import TopicCategory, Region


def get_random_date():
    """ Get a random date between 01-01-1970 and 12-01-2016 """
    return datetime.date(randint(1970,2016), randint(1,12),randint(1,28))


def get_random_category():
    """ Get a random category from GeoNode """
    random_index = randint(0, TopicCategory.objects.all().count() - 1)
    tc = TopicCategory.objects.all()[random_index]
    return tc


def add_random_regions():
    """ Get up to 5 random regions from GeoNode """
    regions = []
    for i in range(0, randint(0, 5)):
        random_index = randint(0, Region.objects.all().count() - 1)
        region = Region.objects.all()[random_index]
        regions.append(region)
    return regions


def add_random_keywords():
    """ Get up to 5 random keywords """
    keywords_list = [
        "geology", "transportation", "utility", "agricolture",
        "idrology", "society", "biology", "industry", "USA",
        "environment", "pollution", "university", "research"
    ]
    keywords = []
    for i in range(0, randint(0, 5)):
        random_index = randint(0, len(keywords_list) - 1)
        keyword = keywords_list[random_index]
        keywords.append(keyword)
    return keywords

def layer2dict(layer):
    """
    Return a json representation for a csw layer.
    """
    wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(layer.bbox_x0, layer.bbox_x1, layer.bbox_y1, layer.bbox_y0)
    layer_dict = {
                    'id': str(layer.uuid),
                    'name': layer.name,
                    'title': layer.title,
                    'abstract': layer.abstract,
                    'bbox': wkt,
                    'category': layer.category.gn_description,
                    'modified_date': layer.date.isoformat() + 'T00:00:00Z',
                    'keywords': [kw for kw in layer.keywords],
                    'regions': [region.name for region in layer.regions],
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


def sync():
    """
    Sync a bunch of csw layers with Solr.
    """

    class cswLayer(object):
        pass

    csw = CatalogueServiceWeb('http://hh.worldmap.harvard.edu/registry/hypermap/csw')
    count = 0
    for startposition in range(0, 2000, 10):
        csw.getrecords2(maxrecords=10, startposition=startposition)
        print csw.results
        for uuid in csw.records:
            record = csw.records[uuid]
            if record.bbox.crs.code == 4326:
                print record.bbox.minx, record.bbox.miny, record.bbox.maxx, record.bbox.maxy
                layer = cswLayer()
                layer.bbox_x0 = float(record.bbox.minx)
                layer.bbox_y0 = float(record.bbox.miny)
                layer.bbox_x1 = float(record.bbox.maxx)
                layer.bbox_y1 = float(record.bbox.maxy)
                if layer.bbox_x0 >= -180 and layer.bbox_x1 <= 180 and layer.bbox_y0 >= -90 and layer.bbox_y1 <= 90:
                    layer.uuid = uuid
                    layer.name = uuid
                    layer.title = record.title
                    layer.abstract = record.abstract
                    layer.url = record.source
                    layer.date = get_random_date()
                    layer.category = get_random_category()
                    layer.regions = add_random_regions()
                    layer.keywords = add_random_keywords()
                    layer_to_solr(layer)
                    print 'Imported record %s' % count
                    count += 1
    print 'Done.'

```

Now run the script using the Django shell:

```sh
$ cd /workshop/geonode/
$ python manage.py shell
>>> from foss4g_scripts import csw2solr
>>> csw2solr.sync()
```

The number of documents in the *boston* Solr core now should be much larger. You can check it at: http://localhost:8983/solr/boston/select?indent=on&q=*:*&wt=json

Note: you may notice that even if index content more than once by running more time the Python scripts, it does not duplicate the results found. This is because the Solr schema for the Boston core specifies a "uniqueKey" field called "id". Whenever you POST commands to Solr to add a document with the same value for the uniqueKey as an existing document, it automatically replaces it for you.

## A quick tour of Solr administrative interface

> Solr features a Web interface that makes it easy for Solr administrators and programmers to view Solr configuration details, run queries and analyze document fields in order to fine-tune a Solr configuration and access online documentation and other help.

Accessing the URL http://hostname:8983/solr/ will show the main **dashboard**. The dashboard displays information related to the Solr, Lucene and Java versions being used, some Java settings and information about the system (such as the physical and the JVM memory)

<img src="images/solr/admin_dashboard.png" alt="Solr admin dashboard" />

From the dashboard it is possible to navigate to other pages of the administrative interface. The **logging** page displays the latest log messages (which are accessible in more complete way using the tail or the less linux command in the shell)

<img src="images/solr/admin_logging.png" alt="Solr admin logging" />

Clicking on the *level* menu it is possible to acces to the **Logging Level** page, from where it is possible to change the logging level

<img src="images/solr/admin_logging_level.png" alt="Solr admin logging level" />

**Core Admin**

<img src="images/solr/admin_core.png" alt="Solr admin core" />

**Java Properties**

<img src="images/solr/admin_java.png" alt="Solr admin Java Properties" />

**Core Overview**

<img src="images/solr/admin_core_overview.png" alt="Solr admin core overview" />

**Core Documents**

<img src="images/solr/admin_core_documents.png" alt="Solr admin core documents" />

**Core Files**

<img src="images/solr/admin_core_files.png" alt="Solr admin core files" />

**Core Query**

<img src="images/solr/admin_core_query.png" alt="Solr admin core query" />

**Core Replication**

<img src="images/solr/admin_core_replication.png" alt="Solr admin core replication" />

**Core Schema**

<img src="images/solr/admin_core_schema.png" alt="Solr admin core schema" />

## Querying Solr

### Keyword matching

Get all of the records: q=*:*

http://localhost:8983/solr/boston/select?&q=*:*

Get all of the records in json:

http://localhost:8983/solr/boston/select?indent=on&q=*:*&wt=json

Paginate records: rows=20&start=50 (rows is 10 by default)

http://localhost:8983/solr/boston/select?indent=on&q=*:*&rows=20&start=50&wt=json

Query a field by exact text: q=title:"Landscape condition"

http://localhost:8983/solr/boston/select?indent=on&q=title:Landscape%20condition&wt=json

Query a field with a wildcard: q=abstract:Natura*

http://localhost:8983/solr/boston/select?indent=on&q=abstract:Natura*&wt=json

Full text query with more parameters: q=_text_:soil% AND _text_:database

http://localhost:8983/solr/boston/select?indent=on&q=_text_:soil%20and%20_text_:database&rows=10&start=0&wt=json

Return only some of the fields: fl=title, abstract

http://localhost:8983/solr/boston/select?fl=title,%20abstract&indent=on&q=*:*&rows=10&start=0&wt=json

Query a multiValued field: regions:Antarctica OR regions:Asia

http://localhost:8983/solr/boston/select?indent=on&q=regions:Antarctica%20or%20regions:Asia&rows=10&start=0&wt=json

Sort by a field: q=*:*&sort=title asc

http://localhost:8983/solr/boston/select?indent=on&q=*:*&sort=title%20asc&wt=json

### Scored results

Getting scored results:

http://localhost:8983/solr/boston/select?fl=*,score&indent=on&q=_text_:geographic&rows=10&start=0&wt=json

### Proximity matching

Lucene supports finding words are a within a specific distance away. Search for "service information" within 4 words from each other: _text_:"service,information"~4

http://localhost:8983/solr/boston/select?indent=on&q=_text_:%22service%20information%22~4&rows=10&start=0&wt=json

### Boosts

Query-time boosts allow one to specify which terms/clauses are "more important". The higher the boost factor, the more relevant the term will be, and therefore the higher the corresponding document scores.

A typical boosting technique is assigning higher boosts to title matches than to body content matches:

(title:service OR title:information)^1.5 (abstract:service OR abstract:information)

http://localhost:8983/solr/boston/select?indent=on&q=(title:*service*%20OR%20title:*information*)^1.5%20(abstract:*service*%20OR%20abstract:*information*)&rows=10&start=0&wt=json

### Date ranges

Getting documents in a date range: q=modified_date:[1970-01 TO 1990-12]

http://localhost:8983/solr/boston/select?indent=on&q=modified_date:[2016-11%20TO%202016-12]&wt=json

Date range syntax can be more complex:

http://localhost:8983/solr/boston/select?indent=on&q=modified_date:[*%20TO%202016-11]&wt=json

### Spatial Search

Search documents by extent:

#### geofilt

The geofilt filter allows you to retrieve results based on the geospatial distance from a given point (a buffer around a point). For example, to find all documents within five kilometers of a given lat/lon point, you could enter &q=*:*&fq={!geofilt sfield=bbox}&pt=45.15,-93.85&d=5

documents Cambridge: Lon: -71.109733 Lat: 42.373616

http://localhost:8983/solr/boston/select?d=1&indent=on&wt=json&q=*:*&fq={!geofilt sfield=bbox}&pt=-71.10,42.37&d=5

#### bbox
The bbox filter is very similar to geofilt except it uses the bounding box of the calculated circle

http://localhost:8983/solr/boston/select?d=1&indent=on&wt=json&q=*:*&fq={!bbox sfield=bbox}&pt=-71.10,42.37&d=5

#### by arbitrary rectangle

&q=*:*&fq=store:[45,-94 TO 46,-93]

http://localhost:8983/solr/boston/select?d=1&indent=on&wt=json&q=*:*&fq=bbox:[-71,42 TO -70,43]

### Facets

#### Keyword facets

http://localhost:8983/solr/boston/select?facet.field=keywords&facet=on&indent=on&q=*:*&rows=10&wt=json

#### Temporal facets

Number of layers per year:

http://localhost:8983/solr/boston/select?q=*:*&facet.range=modified_date&facet=true&facet.range.start=NOW-50YEAR&facet.range.end=NOW&facet.range.gap=%2B1YEAR&wt=json

Number of layers per month:

http://localhost:8983/solr/boston/select?q=*:*&facet.range=modified_date&facet=true&facet.range.start=NOW-50YEAR&facet.range.end=NOW&facet.range.gap=%2B1MONTH&wt=json

#### Spatial facets

Solr spatial field supports generating a 2D grid of facet counts for documents having spatial data in each grid cell.  For high-detail grids, this can be used to plot points, and for lesser detail it can be used for heatmap generation.

http://localhost:8983/solr/boston/select?q=*:*&facet=true&facet.heatmap=bbox&facet.heatmap.geom["-180 -90" TO "180 90"]&wt=json


The minX, maxX, minY, maxY reports the region where the counts are.  This is the minimally enclosing bounding rectangle of the input geom at the target grid level.  This may wrap the dateline. The columns and rows values are how many columns and rows that the output rectangle is to be divided by evenly.  Note: Don't divide an on-screen projected map rectangle evenly to plot these rectangles/points since the cell data is in the coordinate space of decimal degrees if geo=true or whatever units were given if geo=false.  This could be arranged to be the same as an on-screen map but won't necessarily be.
The counts_ints2D key has a 2D array of integers.  The initial outer level is in row order (top-down), then the inner arrays are the columns (left-right).  If any array would be all zeros, a null is returned instead for efficiency reasons.  The entire value is null if there is no matching spatial data.
