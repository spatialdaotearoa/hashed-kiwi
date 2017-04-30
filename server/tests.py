from graphene import Schema
from graphene.test import Client
import unittest

from api import (Query, Mutations)


class MutationTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client(Schema(query=Query, mutation=Mutations))

    def test_mutation_with_point(self):
        query = '''
mutation adminBoundaries {
    createLocation(locationData: {lat: -41.2865, lon: 174.7762}) {
        policeDistrict {
            name
            id
        } dhb {
            name
        } communityBoard {
            name
        }
    }
}
        '''
        executed = self.client.execute(query)
        self.assertEqual(executed, {
            "data": {
                "createLocation": {
                    "policeDistrict": {
                        "name": "Wellington",
                        "id": "12"
                    },
                    "dhb": {
                        "name": "Capital and Coast"
                    },
                    "communityBoard": {
                        "name": None
                    }
                }
            }
        })

    def test_mutation_with_geohash(self):
        query = '''
mutation adminBoundaries {
    createLocation(locationData: {geohash: "rbsm1hh0s"}) {
        policeDistrict {
            name
            id
        } dhb {
            name
        } communityBoard {
            name
        }
    }
}
        '''
        executed = self.client.execute(query)
        self.assertEqual(executed, {
            "data": {
                "createLocation": {
                    "policeDistrict": {
                        "name": "Wellington",
                        "id": "12"
                    },
                    "dhb": {
                        "name": "Capital and Coast"
                    },
                    "communityBoard": {
                        "name": None
                    }
                }
            }
        })


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(MutationTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
