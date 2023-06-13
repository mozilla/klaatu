"""Expected classes for Webdriver Wait."""

import typing
from selenium.webdriver.common.by import By


class firefox_update_banner_is_found(object):
    """Expected class for checking if the update banner is displayed."""

    def __call__(self, driver: typing.Any) -> typing.Any:
        with driver.context(driver.CONTEXT_CHROME):
            driver.find_element(By.ID, "PanelUI-menu-button").click()
            element = driver.find_element(By.CSS_SELECTOR, "#appMenu-popup #appMenu-multiView #appMenu-protonMainView #appMenu-proton-update-banner")
            if element is not None:
                return True
            else:
                return False


class firefox_update_banner_is_invisible(object):
    """Expected class for checking if the update banner is not displayed."""

    def __call__(self, driver: typing.Any) -> typing.Any:
        with driver.context(driver.CONTEXT_CHROME):
            driver.find_element(By.ID, "PanelUI-menu-button").click()
            element = driver.find_element(By.CSS_SELECTOR, "#appMenu-popup #appMenu-multiView #appMenu-protonMainView #appMenu-proton-update-banner")
            if element.is_displayed():
                return False
            else:
                return True
