e#!/usr/bin/env bash
ELASTIC_USER="elastic"
ELASTIC_PASSWD="changeme"
ELASTIC_HOST="localhost:9200"
IN="/data/nz-police-district-boundaries.gpkg"
INDEX_NAME="police-districts"
INDEX_OVERWRITE=0 # Operation will fail if index already exists
MAPPING="/data/$INDEX_NAME-map.txt"
# Write mapping
docker run -v $PWD/data:/data --net=host geographica/gdal2:latest ogr2ogr --config ES_WRITEMAP $MAPPING --config ES_OVERWRITE $INDEX_OVERWRITE -f "elasticsearch" $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST $IN -nln $INDEX_NAME
# PUT in index
docker run -v $PWD/data:/data --net=host geographica/gdal2:latest ogr2ogr --config ES_META $MAPPING --config ES_OVERWRITE $INDEX_OVERWRITE --config ES_BULK 100000 -f "elasticsearch" $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST $IN -nln $INDEX_NAME
# Check it worked (checks an intersection with Wellington)
curl -X POST $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST/$INDEX_NAME/FeatureCollection/_search?pretty=true -d '{
    "query":{
        "bool":{
            "must":{
                "match_all": {}
            },
            "filter":{
                "geo_shape":{
                    "geometry":{
                        "shape":{
                            "type": "Point",
                            "coordinates" : [174.7762, -41.2865]
                        },
                        "relation": "INTERSECTS"
                    }
                }
            }
        }
    }
}' >> $PWD/etl/test-query-$INDEX_NAME.json
