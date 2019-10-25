from datetime import date
import re

import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    base_url = "https://download-installer.cdn.mozilla.net"
    today = date.today()

    # Set correct month for URL builder
    if len(f"{today.month}") < 2:
        current_month = f"0{today.month}"
    else:
        current_month = f"{today.month}"

    # Set correct month for URL builder
    if len(f"{today.day}") < 2 and int(today.day - 5) < 0:
        download_day = "01"
    elif int(today.day) < 15 :
        download_day = f"0{today.day - 5}"
    else:
        download_day = f"{today.day - 5}"

    # if its a new month just grab the 28th day build of last month and build URL
    if int(download_day) < 2:
        download_dir = (
            f"{base_url}/pub/firefox/nightly/{today.year}/0{int(current_month) - 1}/"
        )
        html = requests.get(download_dir)

        soup = BeautifulSoup(html.text, "html.parser")
        page_link = soup.find_all(
            href=re.compile(
                f"{today.year}-0{int(current_month) - 1}-28.*-mozilla-central"
            )
        )
    else:
        download_dir = f"{base_url}/pub/firefox/nightly/{today.year}/{current_month}/"
        html = requests.get(download_dir)

        soup = BeautifulSoup(html.text, "html.parser")
        page_link = soup.find_all(
            href=re.compile(
                f"{today.year}-{current_month}-{download_day}.*-mozilla-central"
            )
        )
    page_link = page_link[1]

    html = requests.get(f'{base_url}{page_link["href"]}')

    soup = BeautifulSoup(html.text, "html.parser")
    download_link = soup.find(href=re.compile(f"firefox-.*.en-US.linux-x86_64.tar.bz2"))
    complete_download_url = f'{base_url}{download_link["href"]}'

    # print to stdout for wget or curl
    print(complete_download_url)
