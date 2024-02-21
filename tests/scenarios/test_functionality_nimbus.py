# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pytest_bdd import given, scenario, then
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@scenario(
    "../features/generic_functionality.feature",
    "The browser's URL bar will navigate to the supplied URL",
)
def test_browser_navigates_to_url_correctly():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    return selenium


@then("Firefox should still accept a URL into the search bar")
def navigate_to_url(selenium):
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
        el.click()
        el.send_keys("https://www.allizom.org/en-US/")
        el.send_keys(Keys.ENTER)


@then("The URL should load the webpage successfully")
def check_url_page_loads_correctly(selenium):
    WebDriverWait(selenium, 60).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".c-navigation-logo-image")),
        message="Navigation logo not found",
    )
