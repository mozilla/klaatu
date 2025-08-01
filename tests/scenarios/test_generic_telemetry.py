# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time

import pytest
import requests
from pytest_bdd import parsers, scenario, scenarios, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


scenarios(
    "../features/withads_search.feature",
    "../features/adclick_search.feature",
    "../features/generic_telemetry.feature",
)


@pytest.mark.xfail(reason="Fails on release due to telemetry restrictions")
@scenario("../features/generic_telemetry.feature", "Report correct telemetry for organic searches")
def test_correct_telemetry_for_organic_searches():
    ...


@pytest.mark.xfail(reason="Fails on release due to telemetry restrictions")
@scenario("../features/adclick_search.feature", "Telemetry reports correctly for background adclick search events")
def test_telemetry_reports_correctly_for_background_adclick_search_events():
    ...


@pytest.mark.xfail(reason="Fails on release due to telemetry restrictions")
@scenario("../features/adclick_search.feature", "Telemetry reports correctly for page history adclick search events")
def test_telemetry_reports_correctly_for_page_history_adclick_search_events():
    ...


@then("The user searches for something in the search bar that will return ads")
def search_using_search_bar_to_return_ads(selenium, enable_search_bar):
    search_box_locator = (By.CSS_SELECTOR, "#search-container .searchbar-textbox")

    enable_search_bar()

    # perform search
    with selenium.context(selenium.CONTEXT_CHROME):
        WebDriverWait(selenium, 60).until(EC.visibility_of_element_located(search_box_locator))
        search_bar = selenium.find_element(*search_box_locator)
        search_bar.send_keys("buy stocks")
        search_bar.send_keys(Keys.ENTER)


@then("The user highlights some text and wants to search for it via the context menu")
def search_using_context_click_menu(selenium, static_server, find_telemetry):
    selenium.get(static_server)
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


@then("The user highlights some text and wants to search for it via the contextmenu")
def search_using_context_click_menu_full(selenium, static_server, find_telemetry):
    """We need to make this a full test in one to avoid server errors."""
    selenium.get(static_server)
    el = selenium.find_element(By.CSS_SELECTOR, "#search-to-return-ads")

    for _ in range(5):
        current_windows = len(selenium.window_handles)
        ActionChains(selenium).move_to_element(el).pause(1).double_click(el).pause(
            1
        ).context_click(el).perform()
        with selenium.context(selenium.CONTEXT_CHROME):
            menu = selenium.find_element(By.CSS_SELECTOR, "#contentAreaContextMenu")
            menu.find_element(By.CSS_SELECTOR, "#context-searchselect").click()
        WebDriverWait(selenium, 60).until(EC.number_of_windows_to_be(current_windows + 1))
        try:
            assert find_telemetry(
                "browser.search.withads.contextmenu", scalar="klaatu:tagged", value=1
            )
        except AssertionError:
            continue
        else:
            return True
    else:
        assert False


@then(parsers.parse("The browser reports correct telemetry for the {search:w} search event"))
def check_telemetry_for_with_ads_search(find_telemetry, search):
    assert find_telemetry(f"browser.search.withads.{search}", scalar="klaatu:tagged", value=1)


@pytest.mark.xfail(reason="Fails on release due to telemetry restrictions")
@then(parsers.parse("The browser reports correct telemetry for the {search:w} adclick event"))
def check_telemetry_for_ad_click_search(find_telemetry, search):
    assert find_telemetry(f"browser.search.adclicks.{search}", scalar="klaatu:tagged", value=1)


@pytest.mark.xfail(reason="Fails on release due to telemetry restrictions")
@then(
    parsers.parse("The browser reports correct provider telemetry for the adclick {tag:w} event")
)
def check_telemetry_for_ad_click_provider_search(find_telemetry, tag):
    assert find_telemetry("browser.search.adclicks.unknown", scalar=f"klaatu:{tag}", value=1)


@pytest.mark.xfail(reason="Fails on release due to telemetry restrictions")
@then(
    parsers.parse("The browser reports correct provider telemetry for the withads {tag:w} event")
)
def check_telemetry_for_with_ads_provider_search(find_telemetry, tag):
    assert find_telemetry("browser.search.withads.unknown", scalar=f"klaatu:{tag}", value=1)


@then(
    parsers.parse(
        "The browser reports correct provider telemetry for the withads {scalar:w} tagged follow on event"  # noqa
    )
)
def check_telemetry_for_tagged_follow_on_search(find_telemetry, scalar):
    assert find_telemetry(
        f"browser.search.withads.{scalar}", scalar="klaatu:tagged-follow-on", value=1
    )


@then(
    parsers.parse(
        "The browser reports correct telemetry of {count:d} for the total URI count event on {window:w} windows"  # noqa
    )
)
def check_telemetry_for_browser_engagement(find_telemetry, count, window):
    if window == "normal":
        assert find_telemetry(
            "browser.engagement.total_uri_count", value=count, scalar_type="scalars"
        )
    else:
        assert find_telemetry(
            "browser.engagement.total_uri_count_normal_and_private_mode",
            value=count,
            scalar_type="scalars",
        )


@then("The user searches for something using the nav bar")
def search_using_url_bar_to_return_ads(navigate_using_url_bar, selenium):
    navigate_using_url_bar(text="stocks")
    logging.info(f"{selenium.current_url}\n")


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
        el.send_keys("stocks")
        ActionChains(selenium).key_down(Keys.ALT).key_down(Keys.SHIFT).key_down(
            Keys.ENTER
        ).perform()
    WebDriverWait(selenium, 60).until(EC.number_of_windows_to_be(4))
    selenium.switch_to.window(selenium.window_handles[-1])


@then("The page is refreshed")
def refresh_page(selenium):
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
    url = selenium.current_url
    selenium.back()
    # wait some time after going back so the event can register
    WebDriverWait(selenium, 30).until(EC.url_changes(url))


@then("The user searches for something")
def load_and_search_on_mozsearch(selenium, search_server):
    url = f"{search_server}/searchTelemetryAd.html?s=test"
    selenium.get(url)


@then("The user clicks on an ad")
def click_on_ad_local_search(selenium):
    time.sleep(10)
    el = selenium.find_element(By.CSS_SELECTOR, "#ad1")
    el.click()
    logging.info(f"Ad URL: {selenium.current_url}\n")


@then("The user triggers a follow-on search")
def trigger_follow_on_search(selenium, search_server):
    url = f"{search_server}/searchTelemetryAd.html?s=test&abc=ff&a=foo"
    selenium.get(url)


@then("The subsession and subsession length is correctly reported")
def check_telemetry_for_subsession_length(ping_server):
    data = requests.get(f"{ping_server}/pings").json()
    assert data[0]["payload"]["info"].get("subsessionLength") is not None
    assert data[0]["payload"]["info"].get("sessionLength") is not None
