import sys
import json

from bs4 import BeautifulSoup
import requests

GENERAL_ELECTORATES_URL = "https://www.parliament.nz/en/mps-and-electorates/members-of-parliament/?PrimaryFilter=General+electorate+seats&SecondaryFilter="
MAORI_ELECTORATES_URL = "https://www.parliament.nz/en/mps-and-electorates/members-of-parliament/?PrimaryFilter=M%C4%81ori+electorate+seats&SecondaryFilter="
PARSER = 'html.parser'
INPUT = zip((
    "General",
    "Maori", ), (
        GENERAL_ELECTORATES_URL,
        MAORI_ELECTORATES_URL, ))

ALL_ELECTORATES = {"General": None, "Maori": None}


def main():

    for electorate_type, url in INPUT:
        response = requests.get(url)
        if not response.status_code == 200:
            raise Exception
        table = BeautifulSoup(response.text, PARSER).find(
            "table", attrs={"class": "table--list"})
        headings = [
            th.get_text().strip() for th in table.find("tr").find_all("th")
        ]
        # Deal with blank headings if any
        for i in range(0, len(headings)):
            if not headings[i]:
                headings[i] = 'heading-{}'.format(i)
        electorate_datums = [
            dict(
                zip(headings, (td.get_text().strip()
                               for td in row.find_all("td"))))
            for row in table.find_all("tr")[1:]
        ]
        ALL_ELECTORATES[electorate_type] = [
            parse_electorate(electorate) for electorate in electorate_datums
        ]

    write_out(ALL_ELECTORATES)
    return


def parse_electorate(electorate):
    TARGET_KEYS_AND_TRANSFORMS = (
        ("Electorate", "electorate_name", lambda x: x),
        ("Surname, Firstname", "mp_name", lambda x: flip_name(x)), )
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
    sys.exit(0)
