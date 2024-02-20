# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

@generic_nimbus
Feature: Generic Functionality smoke tests all pass

    @smoke
    Scenario: The browser's URL bar will navigate to the supplied URL
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should still accept a URL into the search bar
        And The URL should load the webpage sucessfully 
