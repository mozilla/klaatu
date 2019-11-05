from datetime import date
import re

import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    firefox_unbranded_url = "https://wiki.mozilla.org/Add-ons/Extension_Signing"
    html = requests.get(firefox_unbranded_url)
    soup = BeautifulSoup(html.text, "html.parser")
    firefox_builds = []
    for a in soup.find_all("a", href=True):
        if a.text == "Linux":
            firefox_builds.append(a.attrs["href"])
    print(firefox_builds[0])
