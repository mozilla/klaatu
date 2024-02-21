# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import sys

import pytest
from pytest_bdd import given, scenario, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@pytest.fixture
def navigate_using_url_bar(selenium, cmd_or_ctrl_button):
    def _navigate_function(text=None, use_clipboard=False):
        if not text:
            text = "https://www.allizom.org/en-US/"
        with selenium.context(selenium.CONTEXT_CHROME):
            el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
            if use_clipboard:
                ActionChains(selenium).move_to_element(el).pause(1).click().pause(1).key_down(
                    cmd_or_ctrl_button
                ).send_keys("v").key_up(cmd_or_ctrl_button).send_keys(Keys.ENTER).perform()
            else:
                el.click()
                el.send_keys(text)
                el.send_keys(Keys.ENTER)

    return _navigate_function


@scenario(
    "../features/generic_functionality.feature",
    "The browser's URL bar will navigate to the supplied URL",
)
def test_browser_navigates_to_url_correctly():
    pass


@scenario(
    "../features/generic_functionality.feature",
    "The browser's URL bar will navigate to the supplied string",
)
def test_browser_accepts_a_string():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    return selenium


@then("Firefox should still accept a URL into the search bar")
def navigate_to_url(navigate_using_url_bar):
    navigate_using_url_bar()


@then("The URL should load the webpage successfully")
def check_url_page_loads_correctly(selenium):
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".c-navigation-logo-image")),
        message="Navigation logo not found",
    )


@then("Firefox should still accept a copied string that is sent to the search bar")
def copy_and_paste_string_to_url_bar(cmd_or_ctrl_button, selenium, navigate_using_url_bar):
    selenium.get("http://www.allizom.org/en-US/")
    el = selenium.find_element(
        By.CSS_SELECTOR, "section.mzp-c-footer-section:nth-child(1) > h5:nth-child(1)"
    )

    # scroll down to text
    selenium.execute_script("arguments[0].scrollIntoView(true);", el)

    ActionChains(selenium).move_to_element(el).pause(1).double_click(el).key_down(
        cmd_or_ctrl_button
    ).send_keys("c").key_up(cmd_or_ctrl_button).perform()
    navigate_using_url_bar(use_clipboard=True)

    copied_text = el.text
    WebDriverWait(selenium, 60).until(EC.title_contains(el.text))
    search = selenium.find_element(By.CSS_SELECTOR, ".title")
    assert copied_text == search.text
