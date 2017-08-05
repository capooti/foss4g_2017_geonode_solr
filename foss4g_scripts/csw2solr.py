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
