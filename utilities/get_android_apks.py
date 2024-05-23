import argparse
from pathlib import Path

from bs4 import BeautifulSoup
import requests


parser = argparse.ArgumentParser("Options for android apk downloader")

parser.add_argument('--firefox-version', help="The firefox version to download")
args = parser.parse_args()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}
jobs_filter = ["signing-apk-fenix-debug", "signing-apk-fenix-android-test-debug"]
download_ids = {}
task_ids = {}
path = Path().cwd()

firefox_version = args.firefox_version.replace(".", "_")
hg_url = requests.get(f"https://hg.mozilla.org/releases/mozilla-release/rev/FIREFOX-ANDROID_{firefox_version}_RELEASE").content

soup = BeautifulSoup(hg_url, 'html.parser')

treeherder_link = soup.find("a", string='default view')
treeherder_link = treeherder_link.get('href')

revision = treeherder_link.split('=')[-1]

result_id_json = requests.get(f"https://treeherder.mozilla.org/api/project/mozilla-release/push/?full=true&count=10&revision={revision}", headers=headers).json()
result_id = result_id_json.get("results")[0].get("id")

fenix_jobs = requests.get("https://treeherder.mozilla.org/api/project/mozilla-release/jobs/?job_group_symbol=fenix-debug&count=100", headers=headers).json()

for item in fenix_jobs["results"]:
    for job in jobs_filter:
        if item.get("result_set_id") == result_id and job in item.get("job_type_name"):
            download_ids[job] = item.get("id")

for job, id in download_ids.items():
    data = requests.get(f"https://treeherder.mozilla.org/api/project/mozilla-release/jobs/{id}/", headers=headers).json()
    task_ids[job] = data.get("task_id")

test_apk = requests.get(
    f"https://firefox-ci-tc.services.mozilla.com/api/queue/v1/task/{task_ids.get('signing-apk-fenix-android-test-debug')}/runs/0/artifacts/public/build/target.noarch.apk",
    headers=headers
)
fenix_apk = requests.get(
    f"https://firefox-ci-tc.services.mozilla.com/api/queue/v1/task/{task_ids.get('signing-apk-fenix-debug')}/runs/0/artifacts/public/build/target.x86_64.apk",
    headers=headers
)

with open(path.resolve() / f"android-debug-test-v{args.firefox_version}.apk", "wb") as file:
    file.write(test_apk.content)
with open(path.resolve() / f"fenix-debug-v{args.firefox_version}.apk", "wb") as file:
    file.write(fenix_apk.content)

print("APKS DOWNLOADED SUCCESSFULLY!")
