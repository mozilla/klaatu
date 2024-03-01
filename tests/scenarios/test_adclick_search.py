# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from pytest_bdd import parsers, scenarios, then

scenarios("../features/adclick_search.feature")


@then(parsers.parse("The browser reports correct telemetry for the {search:w} adclick event"))
def check_telemetry_for_with_ads_search(find_ads_search_telemetry, search):
    assert find_ads_search_telemetry(
        f"browser.search.adclicks.{search}", ping_data={"google:tagged": 1}
    )
