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
