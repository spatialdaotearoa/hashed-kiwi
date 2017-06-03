import sys
import json
from urllib.parse import urljoin
import time

from bs4 import BeautifulSoup
# Can't use requests because content depends on interation
from selenium import webdriver

ROOT = "https://www.parliament.nz"
GENERAL_ELECTORATES_URL = "{root}/en/mps-and-electorates/members-of-parliament/?PrimaryFilter=General+electorate+seats&SecondaryFilter=".format(
    root=ROOT)
MAORI_ELECTORATES_URL = "{root}/en/mps-and-electorates/members-of-parliament/?PrimaryFilter=M%C4%81ori+electorate+seats&SecondaryFilter=".format(
    root=ROOT)
PARSER = 'html.parser'
INPUT = zip((
    "General",
    "Māori", ), (
        GENERAL_ELECTORATES_URL,
        MAORI_ELECTORATES_URL, ))

ALL_ELECTORATES = {"General": None, "Māori": None}
BROWSER = webdriver.Firefox()  # Could also use a headless PhantomJS


def main():

    for electorate_type, url in INPUT:

        BROWSER.get(url)
        # So, because of lazy loading assets, we actually need to *gradually*
        # scroll to the bottom of the page in order to get all the images to
        # load. So this does 10 discrete scroll movements to reach the bottom.
        steps = 10
        for i in range(0, steps):
            BROWSER.execute_script(
                "window.scrollTo(document.body.scrollHeight/{steps}*{i}, document.body.scrollHeight/{steps}*({i}+1));".
                format(
                    steps=steps, i=i))
        time.sleep(3)  # Delay to allow images to load
        table = BeautifulSoup(BROWSER.page_source, PARSER).find(
            "table", attrs={"class": "table--list"})
        headings = [
            th.get_text().strip() for th in table.find("tr").find_all("th")
        ]
        # Deal with blank headings if any
        for i in range(0, len(headings)):
            if not headings[i]:
                headings[i] = 'heading-{}'.format(i)
        # Parse document table
        electorate_datums = [
            dict(
                zip(headings, (td.get_text().strip()
                               for td in row.find_all("td"))))
            for row in table.find_all("tr")[1:]
        ]
        # Obtain hrefs
        hrefs = [
            dict(
                zip(headings, [
                    d[0].get('href', None) if len(d) else None
                    for d in (td.find_all(
                        'a', href=True)[:1] or {} for td in row.find_all("td"))
                ])) for row in table.find_all("tr")[1:]
        ]
        # Obtain images
        images = [
            dict(
                zip(headings, [
                    d[0].get('src', None) if len(d) else None
                    for d in (td.find_all('img')[:1] or {}
                              for td in row.find_all("td"))
                ])) for row in table.find_all("tr")[1:]
        ]
        ALL_ELECTORATES[electorate_type] = [
            parse_electorate(electorate, url, img)
            for electorate, url, img in zip(electorate_datums, hrefs, images)
        ]

    write_out(ALL_ELECTORATES)
    return


def parse_electorate(electorate, url, image):
    TARGET_KEYS_AND_TRANSFORMS = (
        ("Electorate", "electorate_name", lambda x: x),
        ("Surname, Firstname", "mp", lambda x: {
            "name": flip_name(x),
            'url': urljoin(ROOT, url["Surname, Firstname"]),
            'image': urljoin(ROOT, image['heading-1'].split("?")[0])
        }), )
    return {
        new_k: f(electorate[k])
        for k, new_k, f in TARGET_KEYS_AND_TRANSFORMS
    }


def flip_name(mp_name):
    """
    Borrows, Chester → Chester Borrows
    """
    return " ".join(mp_name.split(", ", 1)[::-1])


def write_out(electorates):
    with open('electorates.json', 'w') as f:
        json.dump(electorates, f, ensure_ascii=False)
    return


if __name__ == '__main__':
    main()
    BROWSER.quit()
    sys.exit(0)
