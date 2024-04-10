# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# script to setup search server
set -ex

git clone https://github.com/mozilla/gecko-dev.git --depth 1

mkdir search_files

cp gecko-dev/browser/components/search/test/browser/telemetry/* search_files/

cp search_server/* search_files/

pip install tox poetry flask
