# hashed-kiwi

GraphQL API for retrieving information about New Zealand geographic administration units given latitude/longitude positions or [geohashes](https://en.wikipedia.org/wiki/Geohash).

**In development.** Incomplete and unstable. Like what you see? Want to help out? Get in touch:
- [@alphabeta_soup](https://twitter.com/alphabeta_soup) on Twitter
- `#loc-aotearoa` channel on [The Spatial Community](http://thespatialcommunity.com/) Slack.

## Running for development

1. Start an Elasticsearch cluster, accessible on `http://localhost:9200` with credentials `elastic:changeme`. See https://github.com/spatialdaotearoa/elasticsearch-docker
2. Load data into this cluster:
  - Unzip included `./data/*.zip` files to a flat structure within `./data` (more data can be added, but the process of using this data isn't entirely automated)
  - Run `./etl/run.sh` (see `./etl/README.md` for more information)
3. Start the GraphQL server (Elasticsearch, Elasticsearch DSL, Graphene, Flask-GraphQL):
```
cd ./server
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
python api.py
```
4. Go to `http://localhost:5000/graphql` to see the Graph*i*QL interface.
  - You can query this, and use introspection as well. Try out this query:
```
mutation point2admin {
  createLocation(locationData: {geohash: "rbsm1hh0s"}) {
    policeDistrict {
      name
    }
    dhb {
      name
      id
    }
  }
}
```
  - The `point2admin` part of the query can actually be any label you want.
  - You can also use a different way of passing a `locationData`:
```
mutation getAadminBoundaryInfoFromLatLng {
  createLocation(locationData: {lon: 174.7762 lat: -41.2865}) {
    policeDistrict {
      name
    }
    dhb {
      name
      id
    }
  }
}
```
  - Currently this `mutation` with `createLocation` is the only way to query the API. It transforms a location (lat/lon or geohash of a point) to the administrative boundaries that the point intersects. Only a small number of boundaries are included in this repository:
    - `policeDistrict` (NZ Police Districts)
    - `dhb` (NZ District Health Boards)
    - `communityBoard` (NZ Community Boards)
  - Note that all of these support `name` and `id`, and nothing else for the present.
  - Also note that `communityBoard` is not defined for all terrestrial areas in NZ. For example, Wellington central does not have a Community Board, so it will respond with `null` for any requested properties.

## Examples

Examples use a location in central Wellington for illustration. You can just take out the string after the `-d` in the `curl` requests and use that in Graph*i*QL.

### Using a GeoJSON point

Request:

```
curl -H 'Content-type: application/graphql -d 'mutation point2admin {
  createLocation(locationData: {lon: 174.7762 lat: -41.2865}) {
    policeDistrict {
      name
    }
    dhb {
      name
      id
    }
    communityBoard {
      name
    }
  }
}' http://localhost:5000/graphql
```

Response (NB: Wellington central does not have a Community Board):

```
{
  "data": {
    "createLocation": {
      "policeDistrict": {
        "name": "Wellington"
      },
      "dhb": {
        "name": "Capital and Coast",
        "id": "14"
      },
      "communityBoard": {
        "name": null
      }
    }
  }
}
```

### Using a geohash

This example uses the same location as the above queries, but this time it is encoded as a geohash. This makes the URL easier to share for simple filters.

Note: this example includes parameters that are hypothetical!

Request:

```
curl -H 'Content-type: application/graphql -d 'mutation point2admin {
  createLocation(locationData: {geohash: "rbsm1hh0s"}) {
    policeDistrict {
      name
      id
    }
    electorate {
      name
      mp {
        name
        phone
        email
        party {
          name
        }
      }
    }
  }
}' http://localhost:5000/graphql
```

Response:

```
{
  "data": {
    "createLocation": {
      "policeDistrict": {
        "name": "Wellington",
        "id": 12
      },
      "electorate": {
        "name": "Wellington Central",
        "mp": {
          "name": "Grant Robertson",
          "phone": "04 801 8079",
          "email": "office@grantrobertson.co.nz",
          "party": {
            "name": "Labour"
          }
        }
      }
    }
  }
}
```

A simple, readily-shareable query to just get the electorate MP's name would be:

```
http://localhost:5000/graphql?query=mutation point2admin{createLocation(locationData:{geohash:"rbsm1hh0s"}){electorate{mp{name}}}&operationName=point2admin
```

Response:

```
{"data":{"electorate":{"mp":{"name":"Grant Robertson"}}}}
```

## How does it work?

#### Briefly

Authority → Spatial data (+linked data) (+metadata) → GDAL/OGR → Elasticsearch → Elasticsearch-DSL/Graphene/Flask-GraphQL → You

(Subject to change.)
