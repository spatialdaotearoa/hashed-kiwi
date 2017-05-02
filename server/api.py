import json

from flask import Flask
from flask_graphql import GraphQLView
import graphene
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime

from search import (Point, GeoHash, query, NORMALISATION)


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

    @staticmethod
    def mutate(root, args, context, info):
        loc_data = args.get('location_data')
        lat, lon = loc_data.get('lat', None), loc_data.get('lon', None)
        if not lat or not lon:
            geohash = loc_data.get('geohash')
            location = GeoHash(geohash)
        else:
            location = Point(lon, lat)

        # TODO use the location to query ES here
        # << BUSINESS LOGIC >>
        get_hits_from_index = lambda hit, index: hit.meta.index == index
        response = query(location)
        _pd, _dhb, _cb, _szs = [
            list(
                filter(lambda hit: get_hits_from_index(hit, index), response))
            for index in [
                'nz-police-district-boundaries',
                'nz-district-health-boards-2012',
                'nz-community-boards-2012-yearly-pattern',
                'nz-school-zones-sept-2010'
            ]
        ]
        # TODO refactor, but allow for flexibility so different boundaries can
        # implement different fields
        pd = {
            'name': _pd[0].properties[NORMALISATION[_pd[0].meta.index]['name']]
            if _pd else None,
            'id': _pd[0].properties[NORMALISATION[_pd[0].meta.index]['id']]
            if _pd else None
        }
        dhb = {
            'name':
            _dhb[0].properties[NORMALISATION[_dhb[0].meta.index]['name']]
            if _dhb else None,
            'id': _dhb[0].properties[NORMALISATION[_dhb[0].meta.index]['id']]
            if _dhb else None
        }
        cb = {
            'name': _cb[0].properties[NORMALISATION[_cb[0].meta.index]['name']]
            if _cb else None,
            'id': _cb[0].properties[NORMALISATION[_cb[0].meta.index]['id']]
            if _cb else None
        }
        szs = [{
            'name': _sz.properties[NORMALISATION[_sz.meta.index]['name']],
            'id': _sz.properties[NORMALISATION[_sz.meta.index]['id']],
            'approvalDate':
            _sz.properties[NORMALISATION[_sz.meta.index]['approvalDate']],
            'effectiveDate':
            _sz.properties[NORMALISATION[_sz.meta.index]['effectiveDate']],
            'type': _sz.properties[NORMALISATION[_sz.meta.index]['type']],
            'office': _sz.properties[NORMALISATION[_sz.meta.index]['office']],
            'underReview':
            _sz.properties[NORMALISATION[_sz.meta.index]['underReview']]
        } for _sz in _szs]

        return CreateLocation(
            policeDistrict=PoliceDistrict(**pd),
            dhb=DHB(**dhb),
            communityBoard=CommunityBoard(**cb),
            schoolZone=[SchoolZone(**sz) for sz in szs])


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
