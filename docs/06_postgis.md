# Spatial query with PostGIS

> PostgreSQL, often simply Postgres, is an open source object-relational database management system (ORDBMS) with an emphasis on extensibility and standards compliance. As a database server, its primary functions are to store data securely and return that data in response to requests from other software applications. PostgreSQL is ACID-compliant and transactional. PostgreSQL has updatable views and materialized views, triggers, foreign keys; supports functions and stored procedures, and other expandability.

> PostGIS is an open source software program that adds support for geographic objects to the PostgreSQL object-relational database. PostGIS follows the Simple Features for SQL specification from the Open Geospatial Consortium (OGC).

There are several good reasons to store the Django database (which by default in your setup uses sqlite) and the vector data uploads database using PostgreSQL and PostGIS. Most notably:

* advanced security and multiuser
* data integrity
* better performances in GeoServer, specially with complex styles
* support for editing layers
* support for spatial SQL

In this step of the workshop you will configure GeoNode to use PostgreSQL/PostGIS for users uploaded layers. You will still keep the Django database in sqlite

Bonus step: uses PostgreSQL for the Django database

## Database creation

Login with the *postgres* user and open **psql**, the PostgreSQL command line utility. If you want to get more acquainted to use psql you can check out [its documentation](https://www.postgresql.org/docs/9.2/static/app-psql.html)

```sh
$ sudo su postgres
postgres@ubuntu-xenial:/workshop$ psql
psql (9.5.7)
Type "help" for help.
```

Create a *geonode* user (role), with the password set to *geonode*. Then create a database, named *geonode* owned by the geonode user: this database will be used by GeoNode to store any shapefile uploaded to it

```sql
postgres=# CREATE ROLE geonode WITH SUPERUSER LOGIN PASSWORD 'geonode';
CREATE ROLE
postgres=# CREATE DATABASE geonode WITH OWNER geonode;
CREATE DATABASE
```

Now connect to the *geonode* database and install the PostGIS extension. Then exit psql

```sql
postgres=# \c geonode
You are now connected to database "geonode" as user "postgres".
geonode=# CREATE EXTENSION postgis;
CREATE EXTENSION
geonode=# \q
exit
```

Make sure you can connect to the *geonode* database using the *geonode* user:

```sh
$ psql -h localhost -U geonode geonode
Password for user geonode:
psql (9.5.7)
SSL connection (protocol: TLSv1.2, cipher: ECDHE-RSA-AES256-GCM-SHA384, bits: 256, compression: off)
Type "help" for help.

geonode=#
```

## Configure GeoNode to use PostgreSQL/PostGIS to store uploaded vector layers:

Now you need to instruct GeoNode to use the *geonode* PostGIS database you just created as a datastore for new uploads.

Open the *local_settings.py* file you previously created and copy and paste the following lines at the beginning of it. Then save the file

```python
import os

import dj_database_url

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = 'sqlite:///{path}'.format(path=os.path.join(PROJECT_ROOT, 'development.db'))
DATASTORE_URL = 'postgis://geonode:geonode@localhost:5432/geonode'

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600),
    'datastore': dj_database_url.parse(DATASTORE_URL, conn_max_age=600),
}

GEOSERVER_LOCATION = os.getenv(
    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
)
GEOSERVER_PUBLIC_LOCATION = os.getenv(
    'GEOSERVER_PUBLIC_LOCATION', 'http://localhost:8080/geoserver/'
)

# OGC (WMS/WFS/WCS) Server Settings
OGC_SERVER = {
    'default': {
        'BACKEND': 'geonode.geoserver',
        'LOCATION': GEOSERVER_LOCATION,
        'LOGIN_ENDPOINT': 'j_spring_oauth2_geonode_login',
        'LOGOUT_ENDPOINT': 'j_spring_oauth2_geonode_logout',
        # PUBLIC_LOCATION needs to be kept like this because in dev mode
        # the proxy won't work and the integration tests will fail
        # the entire block has to be overridden in the local_settings
        'PUBLIC_LOCATION': GEOSERVER_PUBLIC_LOCATION,
        'USER' : 'admin',
        'PASSWORD' : 'geoserver',
        'MAPFISH_PRINT_ENABLED' : True,
        'PRINT_NG_ENABLED' : True,
        'GEONODE_SECURITY_ENABLED' : True,
        'GEOGIG_ENABLED' : False,
        'WMST_ENABLED' : False,
        'BACKEND_WRITE_ENABLED': True,
        'WPS_ENABLED' : False,
        'LOG_FILE': '%s/geoserver/data/logs/geoserver.log' % os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir)),
        # Set to dictionary identifier of database containing spatial data in DATABASES dictionary to enable
        'DATASTORE': 'datastore',
    }
}
```

## Upload data to PostgreSQL/PostGIS

Now upload to GeoNode the following two shapefiles and fill the metadata as suggested below:

* first shapefile path: /workshop/data/shapefiles/CollegesUniversities_Gap.zip
  * Title: "Colleges and Universities in Boston"
  * Abstract: "Colleges and Universities in Boston. Point layer data collected by the Boston Redevelopment Authority."
  * Regions: "United States of America"
  * Keywords: "boston, foss4g2017, education, society"
  * Category: "Society"

* second shapefile path: /workshop/data/shapefiles/bra_planning_districts_2015_zip_pnq.zip
  * Title: "Boston Planning Districts (BRA)"
  * Abstract: "Planning Districts in Boston, as determined by the Boston Redevelopment Authority (BRA)."
  * Regions: "United States of America"
  * Keywords: "boston, foss4g2017, boundaries, planning"
  * Category: "Planning Cadastre"

## Check the new PostGIS store in GeoServer

You can easily check that the new layers are in a PostGIS store. Go to the GeoServer administrative site, and click on the *Layers* menu.

You will see that both the new layers (*geonode:collegesuniversities_gap* and *geonode:bra_planning_districts_2015_zip_pnq*) are in the same store, named *datastore*

<img src="images/0060_geoserver_postgis_store.png" alt="GeoServer PostGIS Store" />

If you click on the *datastore* link, you will get to the *datastore* store page. As you can see it is a PostGIS data store

<img src="images/0060_geoserver_postgis_store_01.png" alt="GeoServer PostGIS Store" />

## A quick tour of PostGIS features

In this step of the tutorial you will have a quick tour of some of the most impressive PostGIS features. If you want to know more about it, two very useful resources are:

* [Introduction to PostGIS workshop, by Boundless](http://workshops.boundlessgeo.com/postgis-intro/)
* [PostGIS documentation](http://postgis.net/docs/manual-dev/)

Connect to the database and check which tables are there with the *\dt* command: the two layers you uploaded should be there, together with the *spatial_ref_sys*, a table needed by PostGIS which is created when you install PostGIS as an extension in the database

```sh
$ psql -h localhost -U geonode geonode
Password for user geonode:
psql (9.5.7)
SSL connection (protocol: TLSv1.2, cipher: ECDHE-RSA-AES256-GCM-SHA384, bits: 256, compression: off)
Type "help" for help.

geonode=# \dt
                        List of relations
 Schema |                Name                 | Type  |  Owner   
--------+-------------------------------------+-------+----------
 public | bra_planning_districts_2015_zip_pnq | table | geonode
 public | collegesuniversities_gap            | table | geonode
 public | spatial_ref_sys                     | table | postgres
(3 rows)
```

When you install PostGIS in the database by using the *CREATE EXTENSION postgis* command you add a number of tables, views and functions on the PostgreSQL database.

The functions enrich the SQL and spatially enable the database. Let's read some of the features of the *bra_planning_districts_2015_zip_pnq* layer using a plain SQL **SELECT** statement:

```sql
geonode=# select * from collegesuniversities_gap limit 5;

 fid |                      the_geom                      | Status | Score | Match_type | Side |      X       |      Y      |               Match_addr                |       ARC_Street        | ARC_City | ARC_State | ARC_ZIP |                   COLLEGE                    |         ADDRESS         |  City  | State | ZIPCODE |    MAIN_TEL    |                URL                 
-----+----------------------------------------------------+--------+-------+------------+------+--------------+-------------+-----------------------------------------+-------------------------+----------+-----------+---------+----------------------------------------------+-------------------------+--------+-------+---------+----------------+------------------------------------
   1 | 0101000020E6100000D0A9ED1E53C651C0E8E8080A992C4540 | M      |   100 | A          | L    | -71.09882628 |  42.3484205 | 700 Beacon St, Boston, MA, 02215        | 700 Beacon Street       | Boston   | MA        | 02215   | Art Institute of Boston at Lesley University | 700 Beacon Street       | Boston | MA    | 02215   | (617) 585-6600 | http://www.aiboston.edu
   2 | 0101000020E610000090F61DBFEBC451C0B88EA1250D2D4540 | M      |   100 | A          | L    | -71.07689257 | 42.35196779 | 122 Commonwealth Ave, Boston, MA, 02116 | 122 Commonwealth Avenue | Boston   | MA        | 02116   | Bay State College                            | 122 Commonwealth Avenue | Boston | MA    | 02116   | (617) 236-8000 | http://www.baystate.edu
   3 | 0101000020E61000006C800F5D81C451C088C1760D452C4540 | M      |   100 | A          | R    | -71.07039302 | 42.34585984 | 41 Berkeley St, Boston, MA, 02116       | 41 Berkeley Street      | Boston   | MA        | 02116   | Benjamin Franklin Institute of Technology    | 41 Berkeley Street      | Boston | MA    | 02116   | (617) 423-4630 | http://www.bfit.edu
   4 | 0101000020E61000000476558EB8C551C06813BAFE632C4540 | M      |   100 | A          | L    | -71.08938998 | 42.34680125 | 1140 Boylston St, Boston, MA, 02215     | 1140 Boylston Street    | Boston   | MA        | 02215   | Berklee College of Music                     | 1140 Boylston Street    | Boston | MA    | 02215   | (617) 266-1400 | http://www.berklee.edu
   5 | 0101000020E6100000E03957391EC651C04810C73CA42C4540 | M      |   100 | A          | L    | -71.09559372 | 42.34875962 | 530 Commonwealth Ave, Boston, MA, 02215 | 530 Commonwealth Ave    | Boston   | MA        | 02215   | Blaine The Beauty Career School-Boston       | 530 Commonwealth Ave    | Boston | MA    | 02215   | (508) 370-7447 | http://www.blainebeautyschools.com
(5 rows)
```

### Querying geometries

You can query PostGIS on the *the_geom* field to detect which is the geometry type of each feature using the **ST_GeometryType** function

```sql
geonode=# select ST_GeometryType(the_geom) from collegesuniversities_gap limit 5;
 st_geometrytype
-----------------
 ST_Point
 ST_Point
 ST_Point
 ST_Point
 ST_Point
(5 rows)
```

Try ST_GeometryType on the *bra_planning_districts_2015_zip_pnq* layer:

```sql
# select ST_GeometryType(the_geom) from bra_planning_districts_2015_zip_pnq limit 5;
 st_geometrytype
-----------------
 ST_MultiPolygon
 ST_MultiPolygon
 ST_MultiPolygon
 ST_MultiPolygon
 ST_MultiPolygon
(5 rows)
```

Now something more fancy: let's get the spatial reference system identifiers for each feature using the **ST_SRID** function

```sql
geonode=# select ST_SRID(the_geom) from collegesuniversities_gap limit 5;
 st_srid
---------
    4326
    4326
    4326
    4326
    4326
(5 rows)
```

```sql
geonode=#  select ST_SRID(the_geom) from bra_planning_districts_2015_zip_pnq limit 5;
 st_srid
---------
    2249
    2249
    2249
    2249
    2249
(5 rows)
```

4326 stands for [EPSG:4326, WGS 84](http://spatialreference.org/ref/epsg/wgs-84/), while 2249 stands for [EPSG:2249, NAD83 / Massachusetts Mainland](http://spatialreference.org/ref/epsg/2249/)

Let's get the centroid and the number of points of each polygon representing a planning district using the **ST_Centroid** and the **ST_NPoints** functions

```sql
geonode=# SELECT ST_Centroid(the_geom), ST_NPoints(the_geom) from bra_planning_districts_2015_zip_pnq limit 5;
                    st_centroid                     | st_npoints
----------------------------------------------------+------------
 0101000020C9080000F27C37839004284155A2E98890974641 |        658
 0101000020C9080000FF0544DB919E274179DE9B37569C4641 |        182
 0101000020C9080000C63CA4EF908527410E33827844894641 |        286
 0101000020C9080000D245B41FA7CC2741F3ED8854527F4641 |        318
 0101000020C9080000063180CD49892741F3905AEEED7F4641 |         71
(5 rows)
```

The geometry is stored as a binary value: it is possible to get a more human friendly representation using one of the geometry outputs function. For example let's get the representation of the geometry of each college/university in the WKT, EWKT, GeoJSON, GML, KML formats:

```sql
geonode=# SELECT ST_AsText(the_geom), ST_AsEWKT(the_geom), ST_AsGeoJSON(the_geom), ST_AsGML(the_geom), ST_AsKML(the_geom) from collegesuniversities_gap limit 5;

                 st_astext                 |                      st_asewkt                      |                            st_asgeojson                             |                                                       st_asgml                                                       |                                     st_askml                                     
-------------------------------------------+-----------------------------------------------------+---------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------
 POINT(-71.0988232918673 42.348420385695)  | SRID=4326;POINT(-71.0988232918673 42.348420385695)  | {"type":"Point","coordinates":[-71.0988232918673,42.348420385695]}  | <gml:Point srsName="EPSG:4326"><gml:coordinates>-71.098823291867348,42.348420385694965</gml:coordinates></gml:Point> | <Point><coordinates>-71.098823291867348,42.348420385694965</coordinates></Point>
 POINT(-71.0768888275727 42.3519637144904) | SRID=4326;POINT(-71.0768888275727 42.3519637144904) | {"type":"Point","coordinates":[-71.0768888275727,42.3519637144904]} | <gml:Point srsName="EPSG:4326"><gml:coordinates>-71.076888827572702,42.35196371449041</gml:coordinates></gml:Point>  | <Point><coordinates>-71.076888827572702,42.35196371449041</coordinates></Point>
 POINT(-71.0703957225211 42.3458573179115) | SRID=4326;POINT(-71.0703957225211 42.3458573179115) | {"type":"Point","coordinates":[-71.0703957225211,42.3458573179115]} | <gml:Point srsName="EPSG:4326"><gml:coordinates>-71.070395722521141,42.345857317911452</gml:coordinates></gml:Point> | <Point><coordinates>-71.070395722521141,42.345857317911452</coordinates></Point>
 POINT(-71.08938940378 42.3468016060422)   | SRID=4326;POINT(-71.08938940378 42.3468016060422)   | {"type":"Point","coordinates":[-71.08938940378,42.3468016060422]}   | <gml:Point srsName="EPSG:4326"><gml:coordinates>-71.08938940377999,42.34680160604222</gml:coordinates></gml:Point>   | <Point><coordinates>-71.08938940377999,42.34680160604222</coordinates></Point>
 POINT(-71.0955947257821 42.3487621280661) | SRID=4326;POINT(-71.0955947257821 42.3487621280661) | {"type":"Point","coordinates":[-71.0955947257821,42.3487621280661]} | <gml:Point srsName="EPSG:4326"><gml:coordinates>-71.095594725782121,42.348762128066085</gml:coordinates></gml:Point> | <Point><coordinates>-71.095594725782121,42.348762128066085</coordinates></Point>
(5 rows)
```

### Transforming data

PostGIS let you transform data from one spatial reference system to another with the **ST_Transform** function.

Here is how you can get the WKT geometry for each district's centroid in both the original EPSG:2249 SRS and the EPSG:4326 SRS

```sql
geonode=# SELECT ST_AsText(ST_Centroid(the_geom)), ST_AsText(ST_Transform(ST_Centroid(the_geom), 4326)) FROM bra_planning_districts_2015_zip_pnq LIMIT 5;
                st_astext                 |                 st_astext                 
------------------------------------------+-------------------------------------------
 POINT(787016.256282715 2961185.06962995) | POINT(-71.0157631183247 42.3726239465675)
 POINT(773960.928253353 2963628.43444425) | POINT(-71.0640300464323 42.3795217918033)
 POINT(770760.468049907 2953864.94147337) | POINT(-71.0760547192716 42.3527748902606)
 POINT(779859.561922247 2948772.66042876) | POINT(-71.0424938530946 42.3386725283588)
 POINT(771236.901368649 2949083.86213886) | POINT(-71.0743804204793 42.3396489642072)
(5 rows)
```

### Editing Geometries

With PostGIS you can run SQL **INSERT** and **UPDATE** commands to add new features or edit existing ones. Here is how to edit the position of the "New England School of Photography" in the *collegesuniversities_gap* layer by using an UPDATE SQL command combined with the **ST_MakePoint** function

```sql
geonode=# SELECT ST_AsText(the_geom) FROM collegesuniversities_gap WHERE "COLLEGE" LIKE '%Photography';
                 st_astext                 
-------------------------------------------
 POINT(-71.0965929732347 42.3489959517937)
(1 row)

geonode=# UPDATE collegesuniversities_gap
geonode=# SET the_geom = ST_SetSRID(ST_MakePoint(-71.0965, 42.3489), 4326)
geonode=# WHERE "COLLEGE" LIKE '%Photography';
geonode=# UPDATE 1

geonode=# SELECT ST_AsText(the_geom) FROM collegesuniversities_gap WHERE "COLLEGE" LIKE '%Photography';
        st_astext        
-------------------------
 POINT(-71.0965 42.3489)
(1 row)
```

### Spatial Joins

One of the most powerful features of PostGIS is the possibility to spatially joins one or more layers. For example you could get a list with colleges and universities for each planning district using the **ST_Contains** function.

As the two layers are using different spatial reference system, you need to transform one of the layer's geometry to the other spatial reference system

```
geonode=# SELECT d."PD" as district, c."COLLEGE" as college
geonode-# FROM bra_planning_districts_2015_zip_pnq as d, collegesuniversities_gap as c
geonode-# WHERE ST_Contains(ST_Transform(d.the_geom, 4326), c.the_geom);
       district       |                      college                       
----------------------+----------------------------------------------------
 Charlestown          | Bunker Hill Community College
 Charlestown          | MGH Institute Of Health Professions
 Back Bay/Beacon Hill | Bay State College
 Back Bay/Beacon Hill | Boston Architectural Center
 Back Bay/Beacon Hill | Butera School Of Art
 Back Bay/Beacon Hill | Fisher College
 Back Bay/Beacon Hill | Gibbs College
 Back Bay/Beacon Hill | Learning Institute For Beauty Sciences
 Back Bay/Beacon Hill | New England College of Optometry
 Back Bay/Beacon Hill | Simmons College
 South End            | Benjamin Franklin Institute of Technology
 Central              | Emerson College
 Central              | Massachusetts General Hospital Dietetic Internship
 Central              | New England College of Finance
 Central              | New England School Of Law
 Central              | North Bennet Street School
 Central              | Northeastern University
 Central              | Suffolk University
 Central              | Tufts University
 Central              | Urban College of Boston
 Fenway/Kenmore       | Art Institute of Boston at Lesley University
 Fenway/Kenmore       | Berklee College of Music
 Fenway/Kenmore       | Blaine The Beauty Career School-Boston
 Fenway/Kenmore       | Boston Conservatory
 Fenway/Kenmore       | Boston University
 Fenway/Kenmore       | Emmanuel College
 Fenway/Kenmore       | Harvard University
 Fenway/Kenmore       | Harvard University
 Fenway/Kenmore       | Massachusetts College of Art
 Fenway/Kenmore       | Massachusetts College of Pharmacy & Health Science
 Fenway/Kenmore       | New England Conservatory of Music
 Fenway/Kenmore       | Northeastern University
 Fenway/Kenmore       | School of the Museum of Fine Arts
 Fenway/Kenmore       | Simmons College
 Fenway/Kenmore       | Simmons College
 Fenway/Kenmore       | Wentworth Institute of Technology
 Fenway/Kenmore       | New England School Of Photography
 Allston/Brighton     | Harvard University
 Allston/Brighton     | Rets Technical Center
 North Dorchester     | University of Massachusetts Boston
 South Dorchester     | Laboure College
 West Roxbury         | Massachusetts School Of Professional Psychology
 Hyde Park            | Boston Baptist College
(43 rows)
```

## Additional resources

* [PostgreSQL Tutorial](http://www.postgresqltutorial.com/)
* [Introduction to PostGIS Workshop](http://workshops.boundlessgeo.com/postgis-intro/) by Boundless
* [The official PostgreSQL documentation](https://www.postgresql.org/docs/9.6/static/index.html)
* [The official PostGIS documentation](http://postgis.net/documentation/)
* [PostGIS functions index](http://postgis.net/docs/manual-2.3/PostGIS_Special_Functions_Index.html)
