#!/usr/bin/env bash
ELASTIC_USER="elastic"
ELASTIC_PASSWD="changeme"
ELASTIC_HOST="localhost:9200"
INDEX_OVERWRITE=0 # Operation will fail if index already exists
INDEX_SHARDS=5
INDEX_REPLICAS=1 # 1 replica for each primary shard)
SIMPLIFICATION_TOLERANCE=0.0001 # https://gis.stackexchange.com/a/8674/25417

# If you need to add a specific attribute filter for a layer, create a hash table
# entry here
declare -A FILTERS
FILTERS=(
  ["nz-community-boards-2012-yearly-pattern"]="Name != 'Area Outside Community'",
  ["nz-urban-areas-2012-yearly-pattern"]="CAST(UA12 AS integer(3)) < 500",
  ["nz-electoral-wards-2012-yearly-pattern"]="WARD12 != '99999'"
)

generate_es_index_template() {
  cat <<EOF
{
  "settings": {
    "number_of_shards": $INDEX_SHARDS,
    "number_of_replicas": $INDEX_REPLICAS
  }
}
EOF
}

task(){
  IN="/data/$(basename $1)"
  INDEX_NAME=$(echo $1 | sed "s/.*\///" | sed "s/\..*//")
  MAPPING="/data/mapping/$INDEX_NAME-map.json"
  WHERE=${FILTERS[$INDEX_NAME]}
  [[ $WHERE = "" ]] && WHERE="1=1" || : # If no where clause, always evaluate to true to include everything
  # Write mapping
  docker run -v $PWD/data:/data --net=host geographica/gdal2:latest ogr2ogr --config ES_WRITEMAP $MAPPING --config ES_OVERWRITE $INDEX_OVERWRITE -f "elasticsearch" $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST $IN -nln $INDEX_NAME
  # PUT index
  curl -X PUT -s -u $ELASTIC_USER:$ELASTIC_PASSWD --data "$(generate_es_index_template)" $ELASTIC_HOST/$INDEX_NAME
  # PUT into index
  docker run -v $PWD/data:/data --net=host geographica/gdal2:latest ogr2ogr -skipfailures -where "$WHERE" -simplify $SIMPLIFICATION_TOLERANCE --config ES_META $MAPPING --config ES_OVERWRITE $INDEX_OVERWRITE --config ES_BULK 100000 -f "elasticsearch" $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST $IN -nln $INDEX_NAME
  # PUT index
  # Check it worked (checks an intersection with Wellington)
  curl -X POST -s $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST/$INDEX_NAME/FeatureCollection/_search?pretty=true -d'{
      "_source": {
        "excludes": [ "geometry" ]
      },
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
  }' > $PWD/etl/test-query-$INDEX_NAME.json
  echo "Task complete"
}

( for f in ./data/*.zip; do
  unzip -o $f -d ./data
done
)

N=2 # Work in batches of N, as background processes
( for f in ./data/*.gpkg; do
  ((i=i%N)); ((i++==0)) && wait
  # Insert into ES, parallelising in batches of $N
  echo "Worker $i ($f) initialised in the background..." & task $f &
done
wait
)

# Load electorate attribute data into ES as a bulk item
curl -X POST -s $ELASTIC_USER:$ELASTIC_PASSWD@$ELASTIC_HOST/_bulk --data-binary @"./electorates/electorates.json"

echo "All work completed"



exit 0
