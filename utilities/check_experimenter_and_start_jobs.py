import json
import os
import re
import subprocess
import time
from dateutil import parser
from packaging.version import parse, Version
from pathlib import Path
from collections import defaultdict

import requests


experimenter_url = "https://experimenter.services.mozilla.com/api/v6/experiments/?=status=Preview"
run_flag = True
testing_list = {}
path = Path().cwd()

def trigger_github_action(slug, branch, firefox_version, workflow_id):
    url = f'https://api.github.com/repos/jrbenny35/klaatu/actions/workflows/{workflow_id}/dispatches'
    inputs = {
        'slug': slug,
        'branch': branch,
        'firefox-version': f"{firefox_version}"
    }

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f"Bearer {os.getenv('BEARER_TOKEN')}" ,
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    data = {
        'ref': 'main',
        'inputs': inputs or {}
    }
    print(f"Running tests for {inputs['slug']}, with data {data}, on workflow {workflow_id}")

    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 204:
        print('Workflow triggered successfully!')
    else:
        print(f'Failed to trigger workflow: {response.status_code}')
        print(response.text)

def get_latest_versions(versions, min_version):
    # Parse versions and group by major.minor

    version_list = []

    from packaging.version import Version
    
    for version in versions.keys():
        if Version(version) >= Version(min_version[0]):
           version_list.append(version)

    version_groups = defaultdict(list)
    for version_str in version_list:
        version = parse(version_str)
        major_minor = f"{version.major}.{version.minor}"
        version_groups[major_minor].append(version)


    # Determine the latest version in each group
    latest_versions = {}
    for major_minor, versions in version_groups.items():
        latest_versions[major_minor] = max(versions, key=lambda v: (v.major, v.minor, v.micro))
    
    # Return the latest versions sorted by major.minor
    return [f"{version}" for version in sorted(latest_versions.values())]

def get_firefox_verions(app_name, channel, min_version):
    test_versions = set()
    versions = requests.get("https://whattrainisitnow.com/api/firefox/releases/").json()
    non_desktop_beta = [f"{Version(list(versions.keys())[-1]).major +1}.0b"]
    
    if "firefox_ios" in app_name:
        # Get list of versions from requested to current based on whattrainisitnow
        for version in reversed(versions.keys()):
            version = Version(version)
            if version.major > Version(min_version).major:
                test_versions.add(version.major)
        if not test_versions: # if the version doesn't exist in whattrainisitnow just return it
           return [f"{Version(min_version)}"]
        else:
            return [f"{_}" for _ in test_versions]
    else:
        match channel:
            case "release":
                test_versions = get_latest_versions(versions, min_version)
                if "desktop" in app_name:
                    test_versions.extend(['latest', 'latest-beta'])
                return test_versions
            case "nightly":
                return "['latest']"
            case "beta":
                if "desktop" in app_name:
                    return "['latest-beta']"
                return non_desktop_beta

# Load string of last experiment
try:
    with open('previous_experiment.txt') as f:
        previous_experiment = f.read()
except FileNotFoundError:
    subprocess.run([f"touch {path}"], encoding="utf8", shell=True)
    previous_experiment = []

# Query Experimenter API
current_experiments = requests.get(experimenter_url).json()

# check if newest experiment is different
if current_experiments[-1]["slug"] not in previous_experiment:
    run_flag = True

#  Exit if the experiment is the same
if not run_flag:
    exit

# Sorted list of experiments that have a publishedDate field
current_experiments = [_ for _ in current_experiments if _['publishedDate'] is not None]
current_experiments = sorted(current_experiments, key=lambda _: parser.isoparse(_.get('publishedDate')))

#  Trigger job based on application
#  Get list of experiments to run tests on
for experiment in reversed(current_experiments):
    if experiment["slug"] != previous_experiment:
        testing_list[experiment["slug"]] = experiment
    else:
        break

for slug, data in testing_list.items():
    ff_version = None
    desktop_workflows = ["windows_manual.yml", "linux_manual.yml"]

    try:
        ff_version = [re.search(r"versionCompare\('(\d+).!'\)", data["targeting"]).group(1)]
    except AttributeError:
        continue  # Don't test experiments with no target version

    match data["appName"]:
        case "firefox_desktop":
            for branch in data["branches"]:
                for workflow_id in desktop_workflows:
                    trigger_github_action(
                        slug, branch["slug"], get_firefox_verions(data["appName"], data["channel"], ff_version), workflow_id
                    )
        case "firefox_ios":
            for branch in data["branches"]:
                workflow_id = "ios_manual.yml"
                _ff_version = Version(ff_version[0])
                trigger_github_action(
                    slug, branch["slug"], get_firefox_verions(data["appName"], data["channel"], f"{_ff_version.major}"), workflow_id
                )
        case "fenix":
            for branch in data["branches"]:
                workflow_id = "android_manual.yml"
                _ff_version = Version(ff_version[0])
                trigger_github_action(
                    slug, branch["slug"], get_firefox_verions(data["appName"], data["channel"], ff_version), workflow_id
                )
    time.sleep(30)
#  Write last experiment to file for next cron run
with open('previous_experiment.txt', 'w') as f:
    f.writelines(current_experiments[-1]["slug"])

print(f"Last experiment tested was {current_experiments[-1]['slug']}")
