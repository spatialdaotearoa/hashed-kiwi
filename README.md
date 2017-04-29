# hashed-kiwi

GraphQL API for retrieving information about New Zealand geographic administration units given latitude/longitude positions or [geohashes](https://en.wikipedia.org/wiki/Geohash).

**In development.** Incomplete and unstable. Like what you see? Want to help out? Get in touch:
- [@alphabeta_soup](https://twitter.com/alphabeta_soup) on Twitter
- `#aotearoa` channel on [The Spatial Community](http://thespatialcommunity.com/) Slack.

## Examples

These are the kind of requests/responses that we'd like to make possible (but aren't yet). Examples use a location in central Wellington for illustration.

### Using a GeoJSON point

Request:

```
curl -X POST http://hashed.kiwi/api/graphql -d '{
  "query": "{
    community-board-2012 {
      name
    }
    district-health-board-2012 {
      name
      source {
        name
        date
      }
    }
  }",
  "operationName": "point",
  "variables": {
    "location": {
      "type: "Point",
      "coordinates": [174.7762, -41.2865]
    }
  }
}'
```

Response (NB: Wellington central does not have a Community Board):

```
{
  "data": {
    "community-board-2012": null,
    "district-health-board-2012": {
      "name": "Capital and Coast",
      "source": {
        "name": "Ministry of Health",
        "date": "2012-08-07"
      }
    }
  },
  "errors": [
    {
      "key": "community-board-2012"
      "message": "No intersecting community-board-2012"
    }
  ]
}
```

### Using a geohash

This example uses the same location as the above queries, but this time it is encoded as a geohash. This makes the URL easier to share for simple filters.

Request:

```
curl -X POST http://hashed.kiwi/api/graphql -d '{
  "query": "{
    police-district {
      name
      id
    }
    electorate-2014 {
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
  }",
  "operationName": "geohash",
  "variables": {
    "location": "rbsm1hh0s"
  }
}'
```

Response:

```
{
  "data": {
    "police-district": {
      "name": "Wellington",
      "id": 12
    },
    "electorate-2014": {
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
```

A simple, readily-shareable query to get just the electorate MP's name would be:

```
curl -X GET http://hashed.kiwi/api/graphql/rbsm1hh0s?query={electorate-2014{mp{name}}}
```

Response:

```
{"data":{"electorate-2014":{"mp":{"name":"Grant Robertson"}}}}
```

## How does it work?

#### Briefly

Authority → Spatial data (+linked data) (+metadata) → GDAL/OGR → Elasticsearch → GraphQL Server → You

(Subject to change.)
