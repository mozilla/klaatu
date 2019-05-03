import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--experiment",
        action="store",
        default=None,
        help="path to experiment XPI needing validation",
    )


@pytest.fixture
def selenium(pytestconfig, selenium):
    """Setup Selenium"""
    addon = pytestconfig.getoption("--experiment")
    selenium.install_addon(os.path.abspath(addon), temporary=True)
    return selenium
