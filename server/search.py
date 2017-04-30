from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
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


def query(location):
    '''Query the Elasticsearch cluster for point intersection against all ES
    indexes (via the special index `_all`).

    args:
        location (`source.Point`, `source.GeoHash`): The location to query for
        intersection

    returns:
        Array of `elasticsearch_dsl.hit`s
    '''
    # TODO by default exclude geometry to make response much faster
    response = Search(using=client, index='_all') \
        .filter("geo_shape", geometry={'relation': 'INTERSECTS', 'shape': location.as_shape()}) \
        .execute()

    # for hit in response:
    #     print(
    #         *[
    #             hit.meta.score, hit.meta.index,
    #             hit.properties[NORMALISATION[hit.meta.index]['name']],
    #             hit.properties[NORMALISATION[hit.meta.index]['id']]
    #         ],
    #         sep='\t')

    return response
