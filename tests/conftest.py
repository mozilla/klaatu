import os
import re
import typing
import json
from zipfile import ZipFile

import pytest

from tests.toolbar import ToolBar


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--experiment",
        action="store",
        default=None,
        help="path to experiment XPI needing validation",
    ),
    parser.addoption(
        "--run-old-firefox",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    )


@pytest.fixture
def firefox_options(
    pytestconfig: typing.Any, firefox_options: typing.Any, experiment_widget_id, request
) -> typing.Any:
    firefox_options.log.level = "trace"
    if pytestconfig.getoption("--run-old-firefox"):
        binary = os.path.abspath("utilities/firefox-old-nightly/firefox/firefox-bin")
        firefox_options.binary = binary
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(f'{os.path.abspath("utilities/klaatu-profile")}')

    firefox_options.set_preference("extensions.install.requireBuiltInCerts", False)
    firefox_options.set_preference("ui.popup.disable_autohide", True)
    firefox_options.set_preference("xpinstall.signatures.required", False)
    firefox_options.set_preference("extensions.webapi.testing", True)
    firefox_options.set_preference("extensions.legacy.enabled", True)
    firefox_options.set_preference("browser.tabs.remote.autostart", True)
    firefox_options.set_preference("browser.tabs.remote.autostart.1", True)
    firefox_options.set_preference("browser.tabs.remote.autostart.2", True)
    firefox_options.set_preference("devtools.chrome.enabled", True)
    firefox_options.set_preference("devtools.debugger.remote-enabled", True)
    firefox_options.set_preference("devtools.debugger.prompt-connection", False)
    firefox_options.set_preference("shieldStudy.logLevel", "All")
    firefox_options.set_preference(f'extensions.{experiment_widget_id}.test.expired', True)
    firefox_options.add_argument("-headless")
    yield firefox_options
    if request.config.option.run_old_firefox:
        with open("utilities/klaatu-profile/user.js", "r+") as f:
            lines = f.readlines()
            f.seek(0)
            for i in lines:
                if i != f'\nuser_pref("extensions.{experiment_widget_id}.test.expired", true);':
                    f.write(i)
            f.truncate()


@pytest.fixture
def firefox_startup_time(firefox: typing.Any) -> typing.Any:
    """Startup with no extension installed"""
    return firefox.selenium.execute_script(
        """
        perfData = window.performance.timing 
        return perfData.loadEventEnd - perfData.navigationStart
        """
    )


@pytest.fixture
def experiment_widget_id(pytestconfig: typing.Any, request: typing.Any) -> typing.Any:
    if not request.node.get_closest_marker("expire_experiment"):
        return

    zip_file = os.path.abspath(pytestconfig.getoption("--experiment"))
    with ZipFile(zip_file) as myzip:
        with myzip.open("manifest.json") as myfile:
            manifest = json.load(myfile)
    widget_id = manifest["applications"]["gecko"]["id"].replace("@", "_").replace(".", "_")
    if request.config.option.run_old_firefox:
        with open("utilities/klaatu-profile/user.js", "a") as f:
            f.write(f'\nuser_pref("extensions.{widget_id}.test.expired", true);')        
    return experiment_widget_id


@pytest.fixture
def addon_ids() -> list:
    return []


@pytest.fixture
def selenium(
    pytestconfig: typing.Any, selenium: typing.Any, addon_ids: list
) -> typing.Any:
    """Setup Selenium"""
    addon = pytestconfig.getoption("--experiment")
    addon_id = selenium.install_addon(os.path.abspath(addon))
    addon_ids.append(addon_id)
    return selenium
