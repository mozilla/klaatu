# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import time

import pytest
from pytest_bdd import given, scenario, then
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.actions.action_builder import ActionBuilder
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
                return
            else:
                el.click()
                el.send_keys(text)
                el.send_keys(Keys.ENTER)
        WebDriverWait(selenium, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loaded"))
        )

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


@scenario(
    "../features/generic_functionality.feature",
    "The browser will allow a new tab to be opened",
)
def test_browser_loads_a_new_tab():
    pass


@scenario(
    "../features/generic_functionality.feature",
    "The browser will allow a new tab to be opened via the keyboard",
)
def test_browser_loads_a_new_tab_via_keyboard():
    pass


@scenario(
    "../features/generic_functionality.feature",
    "The browser will allow language packs to be installed",
)
def test_browser_allows_a_language_pack_to_be_installed():
    pass


@given("Firefox is launched enrolled in an Experiment")
def selenium(selenium):
    selenium.implicitly_wait(5)
    return selenium


@given("Firefox has loaded a webpage")
def load_mozilla_wepage(navigate_using_url_bar, selenium):
    navigate_using_url_bar()
    assert "allizom" in selenium.current_url


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

    WebDriverWait(selenium, 60).until(EC.title_contains(el.text))


@then("Firefox should be allowed to open a new tab")
def open_a_new_tab(selenium):
    with selenium.context(selenium.CONTEXT_CHROME):
        el = selenium.find_element(By.CSS_SELECTOR, "#tabs-newtab-button")
        el.click()


@then("Firefox should be allowed to open a new tab with the keyboard")
def open_a_new_tab_via_keyboard(cmd_or_ctrl_button, selenium):
    with selenium.context(selenium.CONTEXT_CHROME):
        url_bar = selenium.find_element(By.CSS_SELECTOR, "#urlbar-input")
        url_bar.send_keys(cmd_or_ctrl_button, "t")


@then("The tab should open successfully")
def check_new_tab(selenium):
    # get the last tab
    selenium.switch_to.window(selenium.window_handles[-1])
    assert "about:newtab" in selenium.current_url


@then("The user will install a language pack")
def install_acholi_language_pack(selenium, request):

    add_button_locator = (By.CSS_SELECTOR, "#add")
    addon_installed_locator = (By.CSS_SELECTOR, "#appMenu-addon-installed-notification")
    add_to_firefox_locator = (By.CSS_SELECTOR, "#addon-install-confirmation-notification .popup-notification-primary-button")
    browser_dialog_box_locator = (By.CSS_SELECTOR, "#BrowserLanguagesDialog")
    root_dialog_box_locator = (
        By.CSS_SELECTOR,
        "vbox.dialogOverlay:nth-child(1) > vbox:nth-child(1) > browser:nth-child(2)",
    )
    language_button_locator = (By.CSS_SELECTOR, "#manageBrowserLanguagesButton")
    language_search_locator = (By.CSS_SELECTOR, ".in-menulist menuitem label")
    menu_list_locator = (By.CSS_SELECTOR, ".languages-grid #availableLocales .in-menulist")

    if not request.config.getoption("--run-firefox-release"):
        pytest.skip("needs --run-firefox-release option to run")
        return

    # install language pack
    selenium.get("https://addons.mozilla.org/en-US/firefox/addon/acholi-ug-language-pack/")
    selenium.find_element(By.CSS_SELECTOR, ".AMInstallButton-button").click()
    with selenium.context(selenium.CONTEXT_CHROME):
        WebDriverWait(selenium, 60).until(EC.element_to_be_clickable(add_to_firefox_locator))
        time.sleep(5) # need to sleep as the waits sometimes don't work
        selenium.find_element(*add_to_firefox_locator).click()
        WebDriverWait(selenium, 60).until(EC.visibility_of_element_located(addon_installed_locator))

    selenium.get("about:preferences")
    button = selenium.find_element(*language_button_locator)
    button.click()
    WebDriverWait(selenium, 60).until(EC.visibility_of_element_located(root_dialog_box_locator))
    dialog = selenium.find_element(*root_dialog_box_locator)
    selenium.switch_to.frame(dialog)

    dialog = selenium.find_element(*browser_dialog_box_locator)
    menu_list = selenium.find_element(*menu_list_locator)
    menu_list.click()
    WebDriverWait(menu_list, 60).until(EC.visibility_of_element_located(language_search_locator))
    el = menu_list.find_element(*language_search_locator)
    ActionChains(selenium).move_to_element(el).pause(1).click().perform()
    ActionBuilder(selenium).clear_actions()
    menu_list.click()
    language_list = menu_list.find_elements(By.CSS_SELECTOR, "menuitem")
    for item in language_list:
        if "Acholi" in item.get_attribute("label"):
            selenium.execute_script("arguments[0].scrollIntoView(true);", item)  
            ActionChains(selenium).move_to_element(item).pause(1).click().pause(1).perform()
            break
    WebDriverWait(dialog, 60).until(
        EC.element_to_be_clickable(add_button_locator), message="Language was not added"
    )
    dialog.find_element(*add_button_locator).click()

    time.sleep(15)  # need to use a hard wait for the langage pack to download


@then("Firefox will be correctly localized for the installed language pack")
def check_for_localized_firefox(selenium):
    locales_locator = (By.CSS_SELECTOR, "#primaryBrowserLocale")
    text_locator = (By.CSS_SELECTOR, "#browserLanguagesBox > description:nth-child(1)")

    selenium.get("about:preferences")
    locales = selenium.find_element(*locales_locator)
    locales.click()
    list = WebDriverWait(locales, 60).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "menuitem"))
    )
    for item in list:
        if "Acholi" in item.get_attribute("label"):
            ActionChains(selenium).move_to_element(item).pause(1).click().pause(1).perform()
            break
    WebDriverWait(selenium, 60).until(
        EC.text_to_be_present_in_element(
            text_locator,
            "Yer leb ma kitiyo kwedgi me nyuto jami ayera, kwena, ki jami angeya ki ii Firefox.",
        ),
        message="Language switch didn't happen",
    )

    #Xvfb :99 -ac -screen 0 800x600x24 -nolisten tcp &
