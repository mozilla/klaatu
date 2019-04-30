import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--experiment",
        action="store",
        default=None,
        help="path to experiment XPI needing validation",
    )


def selenium(config, selenium):
    addon = config.getoption("--experiment")
    selenium.install_addon(addon)
    return selenium
