# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pytest_bdd import given, scenario, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@scenario(
    "../features/withads_search.feature",
    "Telemetry reports correctly for URL search events",
)
def test_telemetry_reports_for_url_bar_searches():
    pass


@scenario(
    "../features/withads_search.feature",
    "Telemetry reports correctly for search bar search events",
)
def test_telemetry_reports_for_search_bar_searches():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    selenium.implicitly_wait(5)
    return selenium


@given("The user searches for something that is likely to return ads")
def search_using_url_bar_to_return_ads(navigate_using_url_bar):
    navigate_using_url_bar(text="Apple iPhone")


@given("The user searches for something in the search bar that will return ads")
def search_using_search_bar_to_return_ads(selenium):
    pref_list_locator = (By.CSS_SELECTOR, "#prefs tr td span")

    # enable search bar using pref menu since it seems blocked via geckodriver
    selenium.get("about:config")
    pref_search_box = selenium.find_element(By.CSS_SELECTOR, "#about-config-search")
    pref_search_box.click()
    pref_search_box.send_keys("browser.search.widget.inNavBar")
    WebDriverWait(selenium, 60).until(EC.visibility_of_element_located(pref_list_locator))
    pref_list = selenium.find_elements(*pref_list_locator)
    for item in pref_list:
        if item.get_attribute("data-l10n-id") == "about-config-pref-accessible-value-default":
            ActionChains(selenium).move_to_element(item).pause(1).double_click().perform()
            break

    # perform search
    with selenium.context(selenium.CONTEXT_CHROME):
        search_bar = selenium.find_element(By.CSS_SELECTOR, "#search-container .searchbar-textbox")
        search_bar.send_keys("Apple iPhone")
        search_bar.send_keys(Keys.ENTER)


@then("The browser reports correct telemetry for the search event")
def check_telemetry_for_with_ads_url_search(find_ads_search_telemetry):
    find_ads_search_telemetry("browser.search.withads.urlbar", ping_data={"google:tagged": 1})


@then("The browser reports correct telemetry for the searchbar event")
def check_telemetry_for_with_ads_search_bar(find_ads_search_telemetry):
    find_ads_search_telemetry("browser.search.withads.searchbar", ping_data={"google:tagged": 1})
