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
