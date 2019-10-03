import os
import re
import requests
import shutil
import time
import typing
import json
from zipfile import ZipFile

from aiohttp import web
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
        "--run-update-test",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    ),
    parser.addoption(
        "--run-firefox-release",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    ),
    parser.addoption(
        "--private-browsing-enabled",
        action="store_true",
        default=None,
        help="Run older version of firefox",
    )

@pytest.fixture(name="server_url")
def fixture_server_url() -> str:
    """URL where fixture server is located"""
    return "http://0.0.0.0:8080"


@pytest.fixture(name="pings")
def fixture_pings(server_url: typing.AnyStr) -> typing.Any:
    """Factory for managing Ping server interactions"""

    class Pings:
        def get_pings(self) -> typing.List:
            pings: typing.List = []
            timeout = time.time() + 10

            while not pings and time.time() != timeout:
                response = requests.get(f"{server_url}/pings")
                pings = json.loads(response.content)
            return pings

        def delete_pings(self) -> None:
            requests.delete(f"{server_url}/pings")
            return

    return Pings()


@pytest.fixture
def setup_profile(pytestconfig: typing.Any, request: typing.Any) -> typing.Any:
    """"Fixture to create a copy of the profile to use within the test."""
    if pytestconfig.getoption("--run-update-test"):
        shutil.copytree(
            os.path.abspath("utilities/klaatu-profile-old-base"),
            os.path.abspath("utilities/klaatu-profile"),
        )
        return f'{os.path.abspath("utilities/klaatu-profile")}'
    if request.node.get_closest_marker("reuse_profile") and not pytestconfig.getoption(
        "--run-update-test"
    ):
        if pytestconfig.getoption("--run-firefox-release"):
            shutil.copytree(
            os.path.abspath("utilities/klaatu-profile-release-firefox-base"),
            os.path.abspath("utilities/klaatu-profile-release-firefox"),
        )
            return f'{os.path.abspath("utilities/klaatu-profile-release-firefox")}'
        shutil.copytree(
            os.path.abspath("utilities/klaatu-profile-current-base"),
            os.path.abspath("utilities/klaatu-profile-current-nightly"),
        )
        return f'{os.path.abspath("utilities/klaatu-profile-current-nightly")}'



@pytest.fixture
def firefox_options(
    setup_profile: typing.Any,
    pytestconfig: typing.Any,
    firefox_options: typing.Any,
    experiment_widget_id: typing.Any,
    request: typing.Any,
    pings: typing.Any,
) -> typing.Any:
    """Setup Firefox"""
    firefox_options.log.level = "trace"
    if pytestconfig.getoption("--run-update-test"):
        if request.node.get_closest_marker(
            "update_test"
        ):  # disable test needs different firefox
            binary = os.path.abspath(
                "utilities/firefox-old-nightly-disable-test/firefox/firefox-bin"
            )
            firefox_options.binary = binary
            firefox_options.add_argument("-profile")
            firefox_options.add_argument(
                f'{os.path.abspath("utilities/klaatu-profile-disable-test")}'
            )
        else:
            binary = os.path.abspath(
                "utilities/firefox-old-nightly/firefox/firefox-bin"
            )
            firefox_options.binary = binary
            firefox_options.add_argument("-profile")
            firefox_options.add_argument(setup_profile)
    if pytestconfig.getoption("--run-firefox-release"):
        binary = os.path.abspath(
            "utilities/firefox-release/firefox/firefox-bin"
        )
        firefox_options.binary = binary
    if request.node.get_closest_marker("reuse_profile") and not pytestconfig.getoption(
        "--run-update-test"
    ):
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(setup_profile)
    firefox_options.set_preference("extensions.install.requireBuiltInCerts", False)
    firefox_options.set_preference(
        "toolkit.telemetry.server", "http://0.0.0.0:8080/submit/telemetry/"
    )
    firefox_options.set_preference("datareporting.healthreport.uploadEnabled", True)
    firefox_options.set_preference("toolkit.telemetry.log.level", "Trace")
    firefox_options.set_preference("toolkit.telemetry.collectInterval", 10)
    firefox_options.set_preference("toolkit.telemetry.initDelay", 1)
    firefox_options.set_preference("toolkit.telemetry.minSubsessionLength", 0)
    firefox_options.set_preference("datareporting.policy.dataSubmissionEnabled", True)
    firefox_options.set_preference("toolkit.telemetry.log.dump", True)
    firefox_options.set_preference(
        "toolkit.telemetry.testing.disableFuzzingDelay", True
    )
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
    firefox_options.set_preference(
        f"extensions.{experiment_widget_id}.test.expired", True
    )
    # firefox_options.add_argument("-headless")
    yield firefox_options

    # Delete old pings
    pings.delete_pings()

    # Remove old profile
    if (
        request.node.get_closest_marker("reuse_profile")
        and not pytestconfig.getoption("--run-update-test")
        or pytestconfig.getoption("--run-update-test")
    ):
        shutil.rmtree(setup_profile)


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
def manifest_id(pytestconfig: typing.Any) -> str:
    zip_file = os.path.abspath(pytestconfig.getoption("--experiment"))
    with ZipFile(zip_file) as myzip:
        with myzip.open("manifest.json") as myfile:
            manifest = json.load(myfile)
    return str(manifest["applications"]["gecko"]["id"])


@pytest.fixture
def experiment_widget_id(
    pytestconfig: typing.Any, request: typing.Any, manifest_id: str
) -> typing.Any:
    """Experiment's ID"""
    if not request.node.get_closest_marker("expire_experiment"):
        return

    widget_id = manifest_id.replace("@", "_").replace(".", "_")
    if request.config.option.run_update_test:
        with open("utilities/klaatu-profile/user.js", "a") as f:
            f.write(f'\nuser_pref("extensions.{widget_id}.test.expired", true);\n')
    return f"{widget_id}"


@pytest.fixture
def mock_experiment_script() -> typing.Any:
    pass


@pytest.fixture
def addon_ids() -> dict:
    return {}


@pytest.fixture
def selenium(
    pytestconfig: typing.Any, selenium: typing.Any, addon_ids: dict, variables: dict
) -> typing.Any:
    """Setup Selenium"""
    zip_file = os.path.abspath(pytestconfig.getoption("--experiment"))
    with ZipFile(zip_file) as myzip:
        with myzip.open("manifest.json") as myfile:
            manifest = json.load(myfile)
    addon = pytestconfig.getoption("--experiment")
    addon_name = selenium.install_addon(os.path.abspath(addon))
    with selenium.context(selenium.CONTEXT_CHROME):
        addon_id = selenium.execute_script(
            """
            var Cu = Components.utils;
            const {WebExtensionPolicy} = Cu.getGlobalForObject(
                Cu.import("resource://gre/modules/Extension.jsm", this)
            );

            return WebExtensionPolicy.getByID(arguments[0]).mozExtensionHostname;
        """,
            addon_name,
        )
    addon_ids[addon_name] = addon_id
    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.execute_script(
            """
                const { AddonStudies } = ChromeUtils.import(
                    "resource://normandy/lib/AddonStudies.jsm"
                );
                const config = arguments[0];

                async function callit(config) {
                    await AddonStudies.add({
                        recipeId: config.recipeId,
                        slug: config.recipied,
                        userFacingName: config.userFacingName,
                        userFacingDescription: config.userFacingDescription,
                        branch: config.branch,
                        active: true,
                        addonId: config.addonId,
                        addonUrl: config.addonUrl,
                        addonVersion: config.addonVersion,
                        extensionApiId: parseInt(config.extensionApiId),
                        extensionHash: config.extensionHash,
                        hashAlgorithm: config.hashAlgorithm,
                        studyStartDate: new Date(),
                        studyEndDate: null
                    });
                };
                callit(arguments[0]);
            """, variables,
        )
    return selenium
