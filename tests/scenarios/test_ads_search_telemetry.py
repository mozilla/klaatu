# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from pytest_bdd import parsers, scenarios, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

scenarios(
    "../features/withads_search.feature",
    "../features/adclick_search.feature",
    "../features/generic_telemetry.feature",
)


@then("The user searches for something in the search bar that will return ads")
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
        search_bar.send_keys("buy stocks")
        search_bar.send_keys(Keys.ENTER)


@then("The user highlights some text and wants to search for it via the context menu")
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
    selenium.switch_to.window(selenium.window_handles[1])
    time.sleep(5)


@then(parsers.parse("The browser reports correct telemetry for the {search:w} search event"))
def check_telemetry_for_with_ads_search(find_telemetry, search):
    assert find_telemetry(f"browser.search.withads.{search}", ping_data={"google:tagged": 1})


@then(parsers.parse("The browser reports correct telemetry for the {search:w} adclick event"))
def check_telemetry_for_ad_click_search(find_telemetry, search):
    assert find_telemetry(f"browser.search.adclicks.{search}", ping_data={"google:tagged": 1})


@then(
    parsers.parse("The browser reports correct provider telemetry for the adclick {tag:w} event")
)
def check_telemetry_for_ad_click_provider_search(find_telemetry, tag):
    assert find_telemetry("browser.search.adclicks.unknown", ping_data={f"google:{tag}": 1})


@then(
    parsers.parse("The browser reports correct provider telemetry for the withads {tag:w} event")
)
def check_telemetry_for_with_ads_provider_search(find_telemetry, tag):
    assert find_telemetry("browser.search.withads.unknown", ping_data={f"google:{tag}": 1})


@then(
    parsers.parse(
        "The browser reports correct provider telemetry for the withads {scalar:w} tagged follow on event"  # noqa
    )
)
def check_telemetry_for_tagged_follow_on_search(find_telemetry, scalar):
    assert find_telemetry(
        f"browser.search.withads.{scalar}", ping_data={"google:tagged-follow-on": 1}
    )


@then(
    parsers.parse(
        "The browser reports correct telemetry of {count:d} for the total URI count event"
    )
)
def check_telemetry_for_browser_engagement(find_telemetry, count):
    assert find_telemetry(
        "browser.engagement.total_uri_count", ping_data=count, scalar_type="scalars"
    )


@then("The user searches for something that is likely to return ads")
def search_using_url_bar_to_return_ads(navigate_using_url_bar):
    navigate_using_url_bar(text="buy stocks")


@then("The user clicks on an ad")
def click_on_an_ad(selenium):
    current_url = selenium.current_url
    ads = selenium.find_elements(By.CSS_SELECTOR, "#tads a")
    ads[0].click()
    WebDriverWait(selenium, 5).until(EC.url_changes(current_url))


@then("The user should be allowed to search on the new tab")
def search_on_new_tab(selenium):
    search_box = selenium.find_element(By.CSS_SELECTOR, ".search-handoff-button")
    search_box.click()
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
        el.send_keys("buy stocks")
        el.send_keys(Keys.ENTER)


@then("The user should be allowed to perform a background search in the new tab")
def perform_background_search(selenium):
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
        el.send_keys("buy stocks")
        ActionChains(selenium).key_down(Keys.ALT).key_down(Keys.SHIFT).key_down(
            Keys.ENTER
        ).perform()
    WebDriverWait(selenium, 60).until(EC.number_of_windows_to_be(4))
    selenium.switch_to.window(selenium.window_handles[-1])


@then("The page is refreshed")
def refresh_page(selenium):
    # Need to close the browser to get the main ping to send
    selenium.refresh()


@then("The browser is closed")
def close_browser(selenium):
    time.sleep(15)  # wait a little to not cause a race condition
    selenium.quit()


@then("The page loads")
def wait_for_ad_click_page_to_load(selenium):
    WebDriverWait(selenium, 60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body")))


@then("The user goes back to the search page")
def go_back_one_page(selenium):
    selenium.back()
    time.sleep(10)  # wait some time after going back so the event can register


@then("The user searches for something on Google")
def load_and_search_on_google(selenium):
    url = "http://www.google.com"
    selenium.get(url)
    text_box = selenium.find_element(By.CSS_SELECTOR, "form textarea")
    text_box.send_keys("buy stocks", Keys.ENTER)
    WebDriverWait(selenium, 60).until(EC.url_changes(url))


@then("The user triggers a follow-on search")
def trigger_follow_on_search(selenium):
    url = "https://www.google.com/search?client=firefox-b-1-ab&ei=EI_VALUE&q=cheap%20shoes&oq=cheap%20shoes&gs_l=GS_L_VALUE"  # noqa
    selenium.get(url)
