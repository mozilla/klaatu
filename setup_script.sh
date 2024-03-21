set -ex

git clone https://github.com/mozilla/gecko-dev.git --depth 1

mkdir search_files

cp gecko-dev/browser/components/search/test/browser/telemetry/* search_files/

cp search_server/* search_files/
