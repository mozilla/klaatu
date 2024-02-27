# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from pytest_bdd import given, scenario, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@scenario(
    "../features/withads_search.feature",
    "Telemetry reports correctly for URL search events",
)
def test_telemetry_reports_for_url_searched():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    selenium.implicitly_wait(5)
    return selenium


@given("The user searches for something that is likely to return ads")
def search_using_url_bar_to_return_ads(navigate_using_url_bar):
    navigate_using_url_bar(text="Apple iPhone")


@then("The browser reports correct telemetry for the search event")
def check_telemetry_for_with_ads_url_search(find_ads_search_telemetry):
    find_ads_search_telemetry("browser.search.withads.urlbar", ping_data={"google:tagged": 1})
