# OGC Services with GeoServer

Any SDI and geoportal needs to implement OGC Web Services (OWS) and specifications such as:

* [OGC Web Map Service Standard, WMS](http://www.opengeospatial.org/standards/wms)
* [OGC Web Feature Service Standard, WFS](http://www.opengeospatial.org/standards/wfs)
* [OGC Transactional Web Feature Service Standard, WFS-T](http://www.opengeospatial.org/standards/wfs)
* [OGC Web Coverage Service Standard, WCS](http://www.opengeospatial.org/standards/wcs)
* [OGC Web Processing Server Standard, WPS](http://www.opengeospatial.org/standards/wps)
* [OGC Web Map Tile Service Standard, WMTS](http://www.opengeospatial.org/standards/wmts)
* [OSGeo Tile Map Service Specification, TMS](https://wiki.osgeo.org/wiki/Tile_Map_Service_Specification)
* [OSGeo WMS Tile Caching Specification, WMS-C](https://wiki.osgeo.org/wiki/WMS_Tile_Caching) (*)
* [OGC Catalogue Service, CSW](http://www.opengeospatial.org/standards/cat)

(*) superceded by OSGeo TMS and OGC WMTS

All of this services are provided in GeoNode by its underlying [GeoServer](http://geoserver.org/), [GeoWebCache](http://www.geowebcache.org/) and [pycsw](http://pycsw.org/).
It is possible to use [GeoNetwork](http://geonetwork-opensource.org/) in place of pycsw, in case it is needed, by changing the GeoNode default configuration.

GeoServer implements WMS, WFS, WCS, WPS. GeoWebCache implements all of the cache map tiles services: TMS, WMS-C, WMTS. pycsw, or GeoNetwork, implements CSW.

GeoNode, in its end user standard interface, right now makes use of just WMS, WFS, WFS-T, WMS-C and CSW.

WMS, WFS and WFS-T services are provided by GeoServer. WMS-C services are provided by GeoWebCache, as you will see in the next workshop's step. CSW services are provided, as you will see in a following workshop's step, by pycsw.

In this step of the workshop you will take an overview of the GeoServer administrative interface and you will have an overview of the GeoServer OGC services used by GeoNode: WMS and WFS.

You will also use [OWSLib](https://geopython.github.io/OWSLib/), a Python library for interacting with OWS, in order to use these service with the Python language.

Before starting, make sure GeoNode and GeoServer are up and running at: http://localhost:8000/ and http://localhost:8080/geoserver/

If not, activate the virtualenv and run the Django development server:

```sh
$ cd /workshop/
$ . env/bin/activate
$ paver start_geoserver
$ ./manage.py runserver 0.0.0.0:8000
```

## An overview of the GeoServer web administration interface

GeoServer has a browser-based web administration interface application used to configure all aspects of GeoServer, from adding and publishing data to changing service settings.

Accessing the home page of the GeoServer administrative site, at http://localhost:8080/geoserver, on the right side you will see a list of supported standard and specifications

<img src="images/0030_geoserver_home.png" alt="GeoServer Home" />

Clicking on each service capabilities link you will access the capabilities document for the given service type.

A quickstart for using the GeoServer web administration interface can be found [here](http://docs.geoserver.org/latest/en/user/gettingstarted/web-admin-quickstart/index.html). For the purpose of the workshops, takes some minutes to explore the main sections of the GeoServer administrative interface which can be useful when using it with GeoNode. You can access to these sections by clicking on the menu items on the left of the GeoServer page:

*Server Status* provides a summary of the server configuration and status. From this page it is possible to see the location of the GeoServer data directory, the connections and memory used, the JVM Version and many other information

<img src="images/0031_geoserver_server_status.png" alt="GeoServer Server Status" />

*GeoServer Logs* provides the log tail of the GeoServer servlet process. Obviuosly it is possible to access to it from the shell using linux command such as *tail* and *less*

<img src="images/0032_geoserver_logs.png" alt="GeoServer Logs" />

*GeoServer Contact Information* provides a form to set the contact information of the server. This information is used in the metadata provided by the WMS, WCS and WFS GetCapabilities documents.

<img src="images/0033_geoserver_contact_info.png" alt="GeoServer Contact Information" />

*Layer Preview* provides a convenient interface for exploring the layers which have been uploaded to GeoNode/GeoServer. It is possible to browse layers using the OpenLayers viewer, or getting the WMS/WFS response in a specific format

<img src="images/0034_layer_preview_1.png" alt="GeoServer Layer Preview" />

<img src="images/0035_layer_preview_2.png" alt="GeoServer Layer Preview" />

*Workspaces* Analogous to a namespace, a workspace is a container which organizes other items. In GeoServer, a workspace is often used to group similar layers together. By default GeoNode use a workspace named *geonode*, and all of the stores and layers are created within that workspace

<img src="images/0036_geoserver_admin_workspaces.png" alt="GeoServer Workspaces" />

*Stores* A store connects to a data source that contains raster or vector data. A data source can be a file or group of files, a table in a database, a single raster file, or a directory. GeoNode by default will create a GeoTIFF store for each uploaded raster dataset and a Shapefile store for each uploaded vector dataset. It is possible to configure GeoNode to use one or more PostGIS databases and have the vector dataset uploaded as a table in the database. Furthermore, it is possible to use in GeoNode any datasource supported by GeoServer by registering the GeoServer layer in GeoNode with the *updatelayers* management command

<img src="images/0036_geoserver_admin_stores.png" alt="GeoServer Stores" />

<img src="images/0036_geoserver_admin_stores_new.png" alt="GeoServer new store" />

*Layers* provides a view of all of the layers contained in the GeoServer data directory. Layers can be raster or vector datasets. Each layer has a source of data, the *store*, which is associated with the *workspace* in which the store is defined. As you can see the layers you have uploaded to GeoNode are all part of the geonode namespace, and for each one a shapefile store was created

<img src="images/0036_geoserver_admin_layers.png" alt="GeoServer Layers" />

*Styles* provides a view of all of the styles associated (or not) to the layers. By default there is at least one style associated to a layer. One layer can have multiple styles associated to it. Styles can be created using the GeoExplorer interface of GeoNode or the GeoServer admin interface

<img src="images/0036_geoserver_admin_styles.png" alt="GeoServer Styles" />

*WMTS*, *WCS*, *WFS*, *WMS*, *WPS* provide forms to set the service metadata such as the maintainer, title, abstract and other info. One important thing that can be done from this forms is to enable/disable service at global level.

<img src="images/0036_geoserver_admin_services.png" alt="GeoServer Services" />

*Global Settings* provides a way to alter global GeoServer settings, such as the logging level, the behavior with misconfigured layers, the number of decimals to include in output and many others

<img src="images/0036_geoserver_admin_settings.png" alt="GeoServer Global Settings" />

*Tile Caching* you will be back to this in the next workshop step, when you will have a look at GeoWebCache.

*Security* when using GeoServer with GeoNode you shouldn't need to interact with this part of the GeoServer administrative site.

## A gentle introduction to the WMS and WFS OGC standards

In this step of the tutorial you will explore the WMS and WFS OGC standards provided by GeoServer.

### WMS

> The OGC Web Map Service (WMS) specification defines an HTTP interface for requesting georeferenced map images from a server. GeoServer supports WMS 1.1.1, the most widely used version of WMS, as well as WMS 1.3.0.

> WMS provides a standard interface for requesting a geospatial map image. The benefit of this is that WMS clients can request images from multiple WMS servers, and then combine them into a single view for the user. The standard guarantees that these images can all be overlaid on one another as they actually would be in reality. Numerous servers and clients support WMS.

For an extended reference to the WMS standard in GeoServer check the [GeoServer WMS reference documentation](http://docs.geoserver.org/latest/en/user/services/wms/reference.html)

GeoServer implements the following WMS Operations (the last three ones are optional for this standard, but implemented in GeoServer):

* *GetCapabilities*: 	Retrieves metadata about the service, including supported operations and parameters, and a list of the available layers
* *GetMap*: Retrieves a map image for a specified area and content
* *GetFeatureInfo*: Retrieves the underlying data, including geometry and attribute values, for a pixel location on a map
* *DescribeLayer*: Indicates the WFS or WCS to retrieve additional information about the layer
* *GetLegendGraphic*: Retrieves a generated legend for a map
* *GetStyles*: Retrieves a list of styles associated to a layer

All of these WMS operations are used in GeoNode, and you will see how soon: *GetCapabilities* is used to retrieve service and layer metadata, *GetMap* is used any time the GeoNode user update the layers's view in the map composer (GeoExplorer), *GetFeatureInfo* is used any time the GeoNode user identify one or more features from the map composer, *DescribeLayer* is used by the style editor, *GetLegendGraphic* is used to generate the legend elements in the GeoExplorer table of contents, *GetStyles* is used to retrieve the styles associated to a layer

#### GetCapabilities

To see how the WMS GetCapabilities request is composed, and the result of its output, you can click on this link (which is the same link you find in the GeoServer home page for WMS 1.3.0): http://localhost:8080/geoserver/ows?service=wms&version=1.3.0&request=GetCapabilities

Spend some minutes to observer the XML response of this request: you should recognize:

* an initial section with metadata related to the WMS server: name, title, sbstract, keywords, contact information). All of these information may be changed using the GeoServer administrative site
* a section with supported operations: GetCapabilities, GetMap (with the supported output formats), GetFeatureInfo (with the supported output formats)
* a sections with all of the exposed layers and the supported spatial reference system. For each layer the GetCapabilities document returns the name, title, abstract, keywords, bounding box, attribution informations and styles

You should see the four layers which you have uploaded so far to GeoNode, and all of the metadata you compiled.

Now you will use the OWSLib Python library to parse the GetCapabilities document of your GeoNode instance in order to get metadata information about your instance and its layers. Open a new shell, log in the vagrant box, activate the virtualenv and run the Django shell:

```sh
✗ vagrant ssh
$ . /workshop/env/bin/activate
$ cd /workshop/geonode/
$ python manage.py shell
```

Now using Python and OWSLib open the GeoNode WMS endpoint and check its basic metadata:

```python
>>> from owslib.wms import WebMapService
>>> wms = WebMapService('http://localhost:8080/geoserver/ows?') # open GeoNode WMS endpoint
>>> print wms.identification.title # you can change this and the following metadata from GeoServer admin site
My GeoServer WMS
>>> print wms.identification.abstract
This is a description of your Web Map Server.
>>> print wms.identification.keywords
['WFS', 'WMS', 'GEOSERVER']
>>>
```

 Print the WMS supported operation names:

```python
>>> for operation in wms.operations:
        print operation.name # print each WMS operation name

GetCapabilities
GetMap
GetFeatureInfo
DescribeLayer
GetLegendGraphic
GetStyles
```

List service's layers:

```python
>>> list(wms.contents)
['geonode:biketrails_arc_p',
 'geonode:boston_public_schools_2012_z1l',
 'geonode:socioeconomic_status_2000_2014_9p1',
 'geonode:subwaylines_p_odp']
```

Print main information of a layer:

```python
>>> layer = wms['geonode:biketrails_arc_p']
>>> print layer.title
Bike Trails updated
>>> print layer.name
geonode:biketrails_arc_p
>>> print layer.abstract
2009 MBTA bike trails updated
>>> print layer.keywords
['FOSS4G2017', 'commutee']
>>> print layer.boundingBox
(-73.41141983595836, 41.394593205113374, -69.94761156918418, 42.87012688741449, 'EPSG:4326')
```

#### GetMap

The GetMap request can be used to request the WMS endpoint of GeoServer to generate a map. GeoNode use behind the scenes GetMap requests to GeoServer to provide maps to the end users. By default GeoNode, for performance reasons, cache the output of these requests with GeoWebCache, but this beahviour can be changed from the GeoServer administrative interface.

In a WMS GetMap request there are several parameters which are involved, a complete list is [here](http://docs.geoserver.org/stable/en/user/services/wms/reference.html#getmap).

The required parameters for a GetMap request are:

* *service*: always *WMS*
* *version*: Value is one of *1.0.0*, *1.1.0*, *1.1.1*, *1.3.0*
* *request*: always *GetMap*
* *layers*: layers to display on map (comma-separated list of layer names)
* *styles*: styles to use in the map. If empty it uses default styles
* *srs* of *crs*: Spatial Reference System to use in map output, using the EPSG:nnn format
* *bbox* bounding box of the map extent, in the format minx,miny,maxx,maxy
* *width* width of map output in pixels
* *height* height of map output in pixels
* *format* image format for map output

For example here is a GetMap to get a map image of the "Socioeconomic Status (2000-2014)" layer (click on the link to see it): http://localhost:8080/geoserver/wms?LAYERS=geonode%3Asocioeconomic_status_2000_2014_9p1&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&FORMAT=image%2Fpng&SRS=EPSG%3A900913&BBOX=-7915207,5209947,-7910315,5214839&WIDTH=256&HEIGHT=256

An useful way to see build a WMS GetMap request for a layer is by using the GeoServer Layer Preview interface. Go to the GeoServer admin page (http://localhost:8080/geoserver), then click on the *Data > Layer Preview* menu.

Select the layer for which you want to build the WMS GetMap, a format and then the browser will open a new page with the GetMap request in the url

<img src="images/0039_geoserver_layer_preview_getmap.png" alt="GeoServer Layer Preview GetMap" />

Get back now to the Django shell, and you will use OWSLib to perform the same WMS GetMap request programmatically by using Python:

```python
>>> from owslib.wms import WebMapService
>>> wms = WebMapService('http://localhost:8080/geoserver/ows?')
>>> img = wms.getmap(
   ...:     layers=['geonode:socioeconomic_status_2000_2014_9p1'],
   ...:     srs='EPSG:900913',
   ...:     bbox=(-7915207,5209947,-7910315,5214839),
   ...:     size=(256, 256),
   ...:     format='image/png'
   ...: )
>>> out_img = open('/workshop/test_get_map.png', 'wb')
>>> out_img.write(img.read())
>>> out_img.close()
```

Make sure your image has been correctly generated at */workshop/test_get_map.png*. You can easily open it on your host OS by going to the directory where you cloned the workshop repository.

#### GetFeatureInfo

The GeoServer WMS GetFeatureInfo request is used by GeoNode to query return the spatial and attribute data for the features at a given location on a map. For this purpose an alternative could be to use the WFS GetFeatureInfo request, but the GetMap GetFeatureInfo request provide the advantage that request uses an (x, y) pixel value from a returned WMS image.

In a WMS GetFeatureInfo request there are several parameters which are involved, a complete list is [here](http://docs.geoserver.org/stable/en/user/services/wms/reference.html#getfeatureinfo).

The required parameters for a GetFeatureInfo request are very similar to the ones you have used for the GetMap request. Differences are:

* *request*: always *GetFeatureInfo*
* *query_layers*: a comma-separated list of one or more layers to query
* *x* or *i*: X ordinate of query point on map, in pixels. 0 is left side. i is the parameter key used in WMS 1.3.0
* *y* or *j*: Y ordinate of query point on map, in pixels. 0 is the top. j is the parameter key used in WMS 1.3.0
* *info_format*: Format of the response, can be TEXT, GML2, GML3, HTML, JSON, JSONP. This is optional, default is TEXT

Here is a sample GetFeatureInfo request to the socioeconomic_status_2000_2014_9p1 layer. Click on the link to check the GeoServer response:

http://localhost:8080/geoserver/wms?LAYERS=geonode:socioeconomic_status_2000_2014_9p1&QUERY_LAYERS=geonode:socioeconomic_status_2000_2014_9p1&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&BBOX=-7921478,5202230,-7900993,5214785&HEIGHT=657&WIDTH=1072&FORMAT=image/png&INFO_FORMAT=application/json&SRS=EPSG:900913&X=489&Y=376

#### DescribeLayer

GeoExplorer, the client in GeoNode, needs to know the structure of the data, for example to implement the style editor widget and the query widget. This is done using a WMS DescribeLayer to GeoServer.

The required parameters are:

* *service*: always *WMS*
* *version*: Value is one of *1.0.0*, *1.1.0*, *1.1.1*, *1.3.0*
* *request*: always *DescribeLayer*
* *layers*: layers to display on map (comma-separated list of layer names)

Here is a sample DescribeLayer request to the socioeconomic_status_2000_2014_9p1 layer. Click on the link to check the GeoServer response:

http://localhost:8080/geoserver/wms?LAYERS=geonode%3Asocioeconomic_status_2000_2014_9p1&SERVICE=WMS&VERSION=1.1.1&REQUEST=DescribeLayer&outputFormat=text/xml

The output will return the GeoServer service type (WFS for vector layers, WCS for coverage) endpoint to use for getting more information about the layer.

In this case it is a WFS. In a following section you will have a look at how to interact with WFS in GeoServer.

#### GetLegendGraphic

The WMS GetLegendGraphic operation is used by GeoNode to generate the legends in the map composer and in the layer page.

Here is the GetLegendGraphic request for the "Socioeconomic Status (200-2014)" layer:

http://localhost:8080/geoserver/wms?TRANSPARENT=TRUE&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetLegendGraphic&TILED=true&LAYER=geonode:socioeconomic_status_2000_2014_9p1&transparent=true&format=image/png

GetLegendGraphic supports a large number of parameters and options to let a client to generate a great legend graphic. For a full list you can have a read [here](http://docs.geoserver.org/stable/en/user/services/wms/get_legend_graphic/index.html#get-legend-graphic)


#### GetStyles

The WMS GetStyles operation is used by GeoNode to retrieve the list of styles associated to a layer.

Here is the GetStyles request for the "" Socioeconomic Status (200-2014)" layer:

http://localhost:8080/geoserver/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&LAYERS=geonode:socioeconomic_status_2000_2014_9p1

### WFS

> The Web Feature Service (WFS) is a standard created by the Open Geospatial Consortium (OGC) for creating, modifying and exchanging vector format geographic information on the Internet using HTTP. A WFS encodes and transfers information in Geography Markup Language (GML), a subset of XML. The current version of WFS is 2.0.0. GeoServer supports versions 2.0.0, 1.1.0, and 1.0.0. Although there are some important differences between the versions, the request syntax often remains the same.

> The WFS standard defines the framework for providing access to, and supporting transactions on, discrete geographic features in a manner that is independent of the underlying data source. Through a combination of discovery, query, locking, and transaction operations, users have access to the source spatial and attribute data in a manner that allows them to interrogate, style, edit (create, update, and delete), and download individual features. The transactional capabilities of WFS also support the development and deployment of collaborative mapping applications.

For an extended reference to the WFS standard in GeoServer check the [GeoServer WFS reference documentation](http://docs.geoserver.org/latest/en/user/services/wfs/reference.html)

GeoNode uses the version 1.1.0 of the WFS standard, for which GeoServer implements the following operations (the last three ones are optional for this standard, but implemented in GeoServer):

*GetCapabilities* retrieves metadata about the service, including supported operations and parameters, and a list of the available vector layers
*DescribeFeatureType* returns a description of feature types supported by a WFS service
*GetFeature* returns a selection of features from a data source including geometry and attribute values
*LockFeature* prevents a feature from being edited through a persistent feature lock
*Transaction* Edits existing feature types by creating, updating, and deleting

GeoNode implements all of these operations but not the LockFeature: GetCapabilities is used to retrieve service and layers metadata, DescribeFeatureType everytime a layer is activated to read the information of the layer attributes (field name, type...), GetFeature and Transaction when using the editing tools.

## The GeoServer REST API
