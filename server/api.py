import json
from collections import namedtuple

from flask import Flask
from flask_graphql import GraphQLView
import graphene
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime

from search import (Point, GeoHash, query, get, NORMALISATION)


def es_geo_index_result(hits, allow_multiple):
    if not hits:
        return False
    return hits[slice(None)] if allow_multiple else hits[0]


def get_es_props(esindex, props):
    if isinstance(esindex, list):
        return [get_es_props(idx, props) for idx in esindex]
    else:
        return {
            prop: esindex.properties[NORMALISATION[esindex.meta.index][prop]]
            if esindex else None
            for prop in props
        }


class LocationInput(graphene.InputObjectType):
    lat = graphene.Float()
    lon = graphene.Float()
    geohash = graphene.String()


# http://docs.graphene-python.org/en/latest/types/mutations/
class CreateLocation(graphene.Mutation):
    class Input:
        location_data = graphene.Argument(LocationInput)

    policeDistrict = graphene.Field(lambda: PoliceDistrict)
    dhb = graphene.Field(lambda: DHB)
    communityBoard = graphene.Field(lambda: CommunityBoard)
    schoolZone = graphene.List(lambda: SchoolZone)
    postCode = graphene.Field(lambda: PostCode)
    electorate2014 = graphene.Field(lambda: Electorate2014)

    @staticmethod
    def mutate(root, args, context, info):
        loc_data = args.get('location_data')
        lat, lon = loc_data.get('lat', None), loc_data.get('lon', None)
        if not lat or not lon:
            geohash = loc_data.get('geohash')
            location = GeoHash(geohash)
        else:
            location = Point(lon, lat)

        # << BUSINESS LOGIC >>
        get_hits_from_index = lambda hit, index: hit.meta.index == index
        get_props_for_index = lambda index: [key for key in NORMALISATION[index].keys() if not key.startswith('_')]
        response = query(location)
        pd, dhb, cb, szs, post, elec14 = [
            get_es_props(
                es_geo_index_result(
                    list(
                        filter(lambda hit: get_hits_from_index(hit, index),
                               response)),
                    NORMALISATION[index]['_allow_multiple']),
                get_props_for_index(index))
            for index in [
                'nz-police-district-boundaries',
                'nz-district-health-boards-2012',
                'nz-community-boards-2012-yearly-pattern',
                'nz-school-zones-sept-2010',
                'nz-post-postcode-boundaries-june-2011-licensed-only-for-mix-',
                'general-electoral-district-boundaries-2014'
            ]
        ]

        return CreateLocation(
            policeDistrict=PoliceDistrict(**pd),
            dhb=DHB(**dhb),
            communityBoard=CommunityBoard(**cb),
            schoolZone=[SchoolZone(**sz) for sz in szs],
            postCode=PostCode(**post),
            electorate2014=Electorate2014(**elec14))


class Mutations(graphene.ObjectType):
    create_location = CreateLocation.Field()


class AdminBoundary(graphene.Interface):
    name = graphene.String(description="Name of the administrative boundary")
    id = graphene.ID(
        description="Numerical index of the administrative boundary")

    # area = graphene.Float() # Derived from shape
    # geom = JSONString()  # GeoJSON

    def resolve_name(self, args, context, info):
        return self.name

    def resolve_id(self, args, context, info):
        return self.id

    def resolve_geom(self, args, context, info):
        return self.geom


class PoliceDistrict(graphene.ObjectType):
    class Meta:
        interfaces = (AdminBoundary, )

    # # Add additonal bespoke fields here
    # phone = graphene.String()

    # def resolve_phone(self, args, context, info):
    #     return self.phone


class SchoolZone(graphene.ObjectType):
    class Meta:
        interfaces = (AdminBoundary, )

    approvalDate = DateTime()
    effectiveDate = DateTime()
    type = graphene.String(
        description="Type of school (secondary, primary, etc.)")
    office = graphene.String()
    underReview = graphene.String()

    def resolve_approvalDate(self, args, context, info):
        return self.approvalDate

    def resolve_effectiveDate(self, args, context, info):
        return self.effectiveDate

    def resolve_type(self, args, context, info):
        return self.type

    def resolve_office(self, args, context, info):
        return self.office

    def resolve_underReview(self, args, context, info):
        return self.underReview


class PostCode(graphene.ObjectType):
    postcode = graphene.String(description="Four-digit postcode")

    def resolve_postcode(self, args, context, info):
        return self.postcode


class ElectorateMP2014(graphene.ObjectType):
    name = graphene.String(description="Name of the MP")
    url = graphene.String(description="Link to more information about the MP")
    image = graphene.String(description="An image of the MP")
    party = graphene.String(description="The political party of the MP")

    # TODO can use a filter path to filter results in one query
    # rather than make one per attribute! https://elasticsearch-py.readthedocs.io/en/master/api.html#response-filtering
    # http://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html#queries`

    def resolve_name(self, args, context, info):
        return self.name

    def resolve_url(self, args, context, info):
        return self.url

    def resolve_image(self, args, context, info):
        return self.image

    def resolve_party(self, args, context, info):
        return self.party


class Electorate2014(graphene.ObjectType):
    class Meta:
        interfaces = (AdminBoundary, )

    mp = graphene.Field(
        ElectorateMP2014,
        description="The Member of Parliament (General Electorate)")

    def resolve_mp(self, args, context, info):
        MP = namedtuple('MP', ['name', 'url', 'image', 'party'])
        result = get('electorates', self.name, 'General')['_source']
        return MP(result['mp']['name'], result['mp']['url'],
                  result['mp']['image'], result['party'])


class DHB(graphene.ObjectType):
    class Meta:
        interfaces = (AdminBoundary, )


class CommunityBoard(graphene.ObjectType):
    class Meta:
        interfaces = (AdminBoundary, )


class Query(graphene.ObjectType):
    policeDistrict = graphene.Field(
        PoliceDistrict, description="NZ Police District")
    ommunityBoard = graphene.Field(
        CommunityBoard, description="NZ Community Board (2012)")
    dhb = graphene.Field(DHB, description="NZ District Health Board (2012)")
    schoolZone = graphene.Field(SchoolZone, description="NZ School Zone")
    postCode = graphene.Field(PostCode, description="NZ Postal Code")
    electorate2014 = graphene.Field(
        Electorate2014, description="2014 NZ General Electorate")


app = Flask(__name__)
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=graphene.Schema(
            query=Query, mutation=Mutations),
        graphiql=True))

if __name__ == '__main__':
    app.run()
