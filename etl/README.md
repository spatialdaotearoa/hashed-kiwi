# extract-transform-load

In this subdirectory there is a script to be run to process input data from authoritative sources, and load it into Elasticsearch (ES) using OGR.

## Instructions

- Have some data in `./data/` (relative to the project root). (Currently assumes `*.gpkg` but this can easily be adjusted if necessary).
- Start up an ES cluster so that it's available at `localhost:9200` (see `spatialdataotearoa/elasticsearch-docker` for one).
- Run `./etl/run.sh` (assumes `bash`). (Might need to `chmod +x ./etl/run.sh` first, I don't know if permissions are carried with git.)

This will loop through `./data/` and create indexes matching the file names (minus path and extension). Each file will have a mapping file created for it, and then it will be `PUT` into the ES cluster. This is done in batches of 2 until all files are processed. The script will always exit with status 0 even if there were processing errors at the Elasticsearch or OGR feature level, so look at stdout and the `./etl/test-query*.json` outputs.

If you want to delete all indexes in ES (careful): `curl -XDELETE -u elastic:changeme 'http://localhost:9200/*'`. This might be useful because by default if an index already exists, nothing will be done to that index. Indexes are just named for files. You can also just delete a single index: `curl -XDELETE -u elastic:changeme 'http://localhost:9200/index'`

Note, because the ETL script makes use of a hash table, it requires bash 4+.
