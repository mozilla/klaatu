"""Expected classes for Webdriver Wait."""

import typing


class firefox_update_banner_is_found(object):
    """Expected class for checking if the update banner is displayed."""

    def __call__(self, driver: typing.Any) -> typing.Any:
        with driver.context(driver.CONTEXT_CHROME):
            driver.find_element_by_id("PanelUI-menu-button").click()
            element = driver.find_element_by_css_selector(".panel-banner-item")
            if element.is_displayed():
                return True
            else:
                return False


class firefox_update_banner_is_invisible(object):
    """Expected class for checking if the update banner is not displayed."""

    def __call__(self, driver: typing.Any) -> typing.Any:
        with driver.context(driver.CONTEXT_CHROME):
            driver.find_element_by_id("PanelUI-menu-button").click()
            element = driver.find_element_by_css_selector(".panel-banner-item")
            if element.is_displayed():
                return False
            else:
                return True
