# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

@generic_nimbus
Feature: Generic Nimbus smoke tests all pass

    @smoke
    Scenario: The experiment can unenroll from the about:studies page
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The Experiment is unenrolled via the about:studies page
        And the Experiment is shown as disabled on about:studies page

    @smoke
    Scenario: The experiment can be unenrolled via opting out from studies
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The experiment can be unenrolled via opting out of studies
        And the Experiment is shown as disabled on about:studies page
