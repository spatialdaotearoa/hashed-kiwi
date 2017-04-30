from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, GeoPoint, Q
import geohash as Geohash
import yaml

NORMALISATION = dict()
with open('./normalisation.yml', 'r') as stream:
    NORMALISATION = yaml.load(stream)

client = Elasticsearch('http://elastic:changeme@localhost:9200')


class Point(object):
    def __init__(self, x, y):
        self.x, self.y = x, y

    def as_coordinates(self):
        return [self.x, self.y]

    def as_shape(self):
        return {'coordinates': self.as_coordinates(), 'type': 'Point'}


class GeoHash(Point):
    # Strictly, a geohash is an area, but we just consider the centre
    def __init__(self, geohash):
        self.geohash = geohash
        super(GeoHash, self).__init__(
            *tuple(reversed(Geohash.decode(geohash))))

response = Search(using=client, index='_all') \
    .filter("geo_shape", geometry={'relation': 'INTERSECTS', 'shape': Point(174.7762, -41.2865).as_shape()}) \
    .execute()

response = Search(using=client, index='_all') \
    .filter("geo_shape", geometry={'relation': 'INTERSECTS', 'shape': GeoHash('rbsm1hh0s').as_shape()}) \
    .execute()

for hit in response:
    print(
        *[
            hit.meta.score, hit.meta.index,
            hit.properties[NORMALISATION[hit.meta.index]['name']],
            hit.properties[NORMALISATION[hit.meta.index]['id']]
        ],
        sep='\t')
