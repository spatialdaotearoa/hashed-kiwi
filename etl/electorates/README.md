There is currently no API to get data about electorate representatives in NZ.

In this subdirectory there is a scraper to get that data while we wait for a stable API. It should work and I'm happy to have issues or PRs against it if it does not work in the future.

To run it, you will need to install Geckodriver (Firefox) for Selenium. We can't just use Python's `requests` library (or equivalent) because the assets on the page currently load lazily, so a browser actually needs to load and then scroll down the page. See `setup.sh` for an installation script for Linux.

Then use `requirements.txt` to create a Python 3 virtual environment, and run `python script.py`. This writes data to `electorates.json`, which you can also just download.

The script loads information about both Māori and General electorate MPs:

```
{
  Māori: {electorate_name: String, mp: {name: String, url: String, image: String},
  General: {electorate_name: String, mp: {name: String, url: String, image: String}
}
```

The output JSON is UTF-8.
