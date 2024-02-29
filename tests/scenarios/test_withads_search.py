# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from pytest_bdd import given, parsers, scenarios, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

scenarios("../features/withads_search.feature")


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


@given("The user highlights some text and wants to search for it via the context menu")
def search_using_context_click_menu(selenium, simplehttpserver):
    selenium.get("http://localhost:8000")
    el = selenium.find_element(By.CSS_SELECTOR, "#search-to-return-ads")

    ActionChains(selenium).move_to_element(el).pause(1).double_click(el).pause(1).context_click(
        el
    ).perform()
    with selenium.context(selenium.CONTEXT_CHROME):
        menu = selenium.find_element(By.CSS_SELECTOR, "#contentAreaContextMenu")
        menu.find_element(By.CSS_SELECTOR, "#context-searchselect").click()
    WebDriverWait(selenium, 60).until(EC.number_of_windows_to_be(3))


@then(parsers.parse("The browser reports correct telemetry for the {search:w} search event"))
def check_telemetry_for_with_ads_search(find_ads_search_telemetry, search):
    assert find_ads_search_telemetry(
        f"browser.search.withads.{search}", ping_data={"google:tagged": 1}
    )


@then("The user should be allowed to search on the new tab")
def search_on_new_tab(selenium):
    search_box = selenium.find_element(By.CSS_SELECTOR, ".search-handoff-button")
    search_box.click()
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
        el.send_keys("Apple iphone")
        el.send_keys(Keys.ENTER)


@then("The user should be allowed to perform a background search in the new tab")
def perform_background_search(selenium):
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
        el.send_keys("Apple iphone")
        ActionChains(selenium).key_down(Keys.ALT).key_down(Keys.SHIFT).key_down(
            Keys.ENTER
        ).perform()


@then("The page is refreshed")
def refresh_page_and_close_browser(selenium):
    # Need to close the browser to get the main ping to send
    selenium.refresh()
    time.sleep(15)  # wait a little to not cause a race condition
    selenium.quit()
