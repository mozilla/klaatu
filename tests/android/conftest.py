# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import random
import subprocess
import time
from pathlib import Path

import pytest
import requests
from pytest_metadata.plugin import metadata_key

from .gradlewbuild import GradlewBuild
from .models.models import TelemetryModel

KLAATU_SERVER_URL = "http://localhost:1378"
KLAATU_LOCAL_SERVER_URL = "http://localhost:1378"

here = Path()


def pytest_addoption(parser):
    parser.addoption(
        "--experiment-feature",
        action="store",
        help="Feature name you want to test against",
    )
    parser.addoption(
        "--experiment-branch",
        action="store",
        default="control",
        help="Experiment Branch you want to test on",
    )
    parser.addoption(
        "--experiment-server",
        action="store",
        default="prod",
        help="Experiment Server the experiment is hosted on",
    )
    parser.addoption(
        "--experiment-slug",
        action="store",
        default=None,
        help="Experiment slug from Experimenter",
    )
    parser.addoption(
        "--firefox-version",
        action="store",
        default=None,
        help="The Firefox Version you are testing on. This is just use for reporting",
    )


def pytest_runtest_setup(item):
    envnames = [mark.name for mark in item.iter_markers()]
    if envnames:
        if item.config.getoption("--experiment-feature") not in envnames:
            pytest.skip("test does not match feature name")


def start_process(path, command):
    module_path = Path(path)

    try:
        process = subprocess.Popen(
            command,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=module_path.absolute(),
        )
        stdout, stderr = process.communicate(timeout=5)

        if process.returncode != 0:
            raise Exception(stderr)
    except subprocess.TimeoutExpired:
        logging.info(f"{module_path.name} started")
        return process


@pytest.fixture(name="nimbus_cli_args")
def fixture_nimbus_cli_args():
    return ""


@pytest.fixture(name="experiment_branch", scope="session", autouse=True)
def fixture_experiment_branch(request):
    branch = request.config.getoption("--experiment-branch")
    os.environ["EXPERIMENT_BRANCH"] = branch
    return branch


@pytest.fixture(name="experiment_slug", scope="session", autouse=True)
def fixture_experiment_slug(request):
    slug = request.config.getoption("--experiment-slug")
    os.environ["EXPERIMENT_SLUG"] = slug
    return slug


@pytest.fixture(name="firefox_version", scope="session", autouse=True)
def fixture_firefox_version(request):
    ff_version = request.config.getoption("--firefox-version")
    os.environ["FIREFOX_VERSION"] = ff_version
    return ff_version


@pytest.fixture(name="experiment_server")
def fixture_experiment_server(request):
    return request.config.getoption("--experiment-server")


@pytest.fixture(name="load_branches")
def fixture_load_branches(experiment_url):
    branches = []

    if experiment_url:
        data = experiment_url
    else:
        try:
            data = requests.get(f"{KLAATU_SERVER_URL}/experiment").json()
        except ConnectionRefusedError:
            logging.warn("No URL or experiment slug provided, exiting.")
            exit()
        else:
            for item in reversed(data):
                data = item
                break
    experiment = requests.get(data).json()
    for item in experiment["branches"]:
        branches.append(item["slug"])
    return branches


@pytest.fixture
def gradlewbuild_log(pytestconfig, tmpdir):
    gradlewbuild_log = f"{tmpdir.join('gradlewbuild.log')}"
    pytestconfig._gradlewbuild_log = gradlewbuild_log
    yield gradlewbuild_log


@pytest.fixture
def gradlewbuild(gradlewbuild_log):
    yield GradlewBuild(gradlewbuild_log)


@pytest.fixture(name="experiment_data")
def fixture_experiment_data(experiment_url, request):
    data = requests.get(experiment_url).json()
    logging.debug(f"JSON Data used for this test: {data}")
    return [data]


@pytest.fixture(name="experiment_url", scope="module")
def fixture_experiment_url(request, variables, experiment_slug):
    url = None

    if slug := experiment_slug:
        # Build URL from slug
        match request.config.getoption("--experiment-server"):
            case "prod":
                url = f"{variables['urls']['prod_server']}/api/v6/experiments/{slug}/"
            case "stage" | "stage/preview":
                url = f"{variables['urls']['stage_server']}/api/v6/experiments/{slug}/"
    else:
        try:
            data = requests.get(f"{KLAATU_SERVER_URL}/experiment").json()
        except requests.exceptions.ConnectionError:
            logging.error("No URL or experiment slug provided, exiting.")
            exit()
        else:
            for item in data:
                if isinstance(item, dict):
                    continue
                else:
                    url = item
    yield url
    return_data = {"url": url}
    try:
        requests.put(f"{KLAATU_SERVER_URL}/experiment", json=return_data)
    except requests.exceptions.ConnectionError:
        pass


@pytest.fixture(name="ping_server", autouse=True, scope="session")
def fixture_ping_server():
    process = start_process("ping_server", ["python", "ping_server.py"])
    yield "http://localhost:5000"
    process.terminate()


@pytest.fixture(name="delete_telemetry_pings")
def fixture_delete_telemetry_pings(variables):
    def runner():
        requests.delete(f"{variables['urls']['telemetry_server']}/pings")

    return runner


@pytest.fixture(name="start_app")
def fixture_start_app(run_nimbus_cli_command):
    def _():
        command = "nimbus-cli --app fenix --channel developer open"
        run_nimbus_cli_command(command)
        time.sleep(15)  # Wait a while as there's no real way to know when the app has started

    return _


@pytest.fixture(name="send_test_results", autouse=True)
def fixture_send_test_results():
    yield
    here = Path()

    with open(f"{here.resolve() / 'results' / 'index.html'}", "rb") as f:
        files = {"file": f}
        try:
            requests.post(f"{KLAATU_SERVER_URL}/test_results", files=files)
        except requests.exceptions.ConnectionError:
            pass


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(experiment_slug, variables):
    def _check_ping_for_experiment(branch=None, experiment=experiment_slug, reason=None):
        model = TelemetryModel(branch=branch, experiment=experiment)

        timeout = time.time() + 60 * 5
        while time.time() < timeout:
            data = requests.get(f"{variables['urls']['telemetry_server']}/pings").json()
            events = []
            for item in data:
                event_items = item.get("events")
                if event_items:
                    for event in event_items:
                        if (
                            "category" in event
                            and "nimbus_events" in event["category"]
                            and "extra" in event
                            and "branch" in event["extra"]
                        ):
                            events.append(event)
            for event in events:
                event_name = event.get("name")
                if (reason == "enrollment" and event_name == "enrollment") or (
                    reason == "unenrollment" and event_name in ["unenrollment", "disqualification"]
                ):
                    telemetry_model = TelemetryModel(
                        branch=event["extra"]["branch"],
                        experiment=event["extra"]["experiment"],
                    )
                    if model == telemetry_model:
                        return True
            time.sleep(5)
        return False

    return _check_ping_for_experiment


@pytest.fixture(name="open_app")
def fixture_open_app(run_nimbus_cli_command):
    def _():
        command = "nimbus-cli --app fenix --channel developer open"
        run_nimbus_cli_command(command)
        time.sleep(5)

    return _


@pytest.fixture(name="run_nimbus_cli_command")
def fixture_run_nimbus_cli_command(gradlewbuild_log):
    def _run_nimbus_cli_command(command):
        logging.info(f"Running command {command}")
        try:
            out = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            out = e.output
            logging.info(out)
            raise
        finally:
            with open(gradlewbuild_log, "w") as f:
                f.write(f"{out}")

    return _run_nimbus_cli_command


@pytest.fixture(name="set_experiment_test_name")
def fixture_set_experiment_test_name(experiment_data):
    # Get a random word from the experiments userFacingName attribute.
    exp_name = experiment_data[0]["userFacingName"].split()
    os.environ["EXP_NAME"] = exp_name[random.randint(0, len(exp_name) - 1)]


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    # Add data to html report
    session.config.stash[metadata_key]["Experiment Slug"] = os.environ.get(
        "EXPERIMENT_SLUG", "N/A"
    )
    session.config.stash[metadata_key]["Experiment Branch"] = os.environ.get(
        "EXPERIMENT_BRANCH", "N/A"
    )
    session.config.stash[metadata_key]["Firefox Version"] = os.environ.get(
        "FIREFOX_VERSION", "N/A"
    )


@pytest.fixture(name="setup_experiment")
def fixture_setup_experiment(
    experiment_slug,
    experiment_branch,
    nimbus_cli_args,
    run_nimbus_cli_command,
    set_experiment_test_name,
    delete_telemetry_pings,
    experiment_server,
):
    def _():
        delete_telemetry_pings()
        logging.info(f"Testing experiment {experiment_slug}, BRANCH: {experiment_branch}")
        command = [
            "nimbus-cli",
            "--app fenix",
            "--channel developer",
            f"enroll {experiment_server}/{experiment_slug}",
            f"--branch {experiment_branch}",
            f"--patch {here.resolve() / 'patch.json'}",
            "--reset-app",
            f"{nimbus_cli_args}",
        ]
        run_nimbus_cli_command(" ".join(command))
        time.sleep(15)  # Wait a while as there's no real way to know when the app has started

    return _
