from datetime import date, timedelta
import re

import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    base_url = "https://download-installer.cdn.mozilla.net"
    today = date.today()
    download_date = today - timedelta(weeks=4)
    download_date = download_date.replace(day=15)

    _date = {
        "year": download_date.strftime("%Y"),
        "month": download_date.strftime("%m"),
        "day": download_date.strftime("%d"),
    }

    download_dir = f"{base_url}/pub/firefox/nightly/{_date['year']}/{_date['month']}/"
    html = requests.get(download_dir)

    soup = BeautifulSoup(html.text, "html.parser")
    page_link = soup.find_all(
        href=re.compile(
            f"{_date['year']}-{_date['month']}-{_date['day']}.*-mozilla-central"
        )
    )
    page_link = page_link[1]

    html = requests.get(f"{base_url}{page_link['href']}")

    soup = BeautifulSoup(html.text, "html.parser")
    download_link = soup.find(href=re.compile("firefox-.*.en-US.linux-x86_64.tar.xz"))
    complete_download_url = f"{base_url}{download_link['href']}"

    # print to stdout for wget or curl
    print(complete_download_url)
