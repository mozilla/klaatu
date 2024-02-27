# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

@generic_nimbus
Feature: Generic Functionality smoke tests all pass

    @smoke
    Scenario: The browser's URL bar will navigate to the supplied URL
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should still accept a URL into the search bar
        And The URL should load the webpage successfully 

    @smoke
    Scenario: The browser's URL bar will navigate to the supplied string
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should still accept a copied string that is sent to the search bar

    @smoke
    Scenario: The browser will allow a new tab to be opened
        Given Firefox is launched enrolled in an Experiment
        And Firefox has loaded a webpage
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully

    @smoke
    Scenario: The browser will allow a new tab to be opened via the keyboard
        Given Firefox is launched enrolled in an Experiment
        And Firefox has loaded a webpage
        Then Firefox should be allowed to open a new tab with the keyboard
        And The tab should open successfully

    @smoke
    Scenario: The browser will allow language packs to be installed
        Given Firefox is launched enrolled in an Experiment
        Then The user will install a language pack
        And Firefox will be correctly localized for the installed language pack
