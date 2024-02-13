# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

@generic_nimbus
Feature: Generic Nimbus smoke tests all pass

    @smoke
    Scenario: The browser will enroll into the requested branch
        Given Firefox is launched enrolled in an Experiment
        Then The experiment branch should be correctly reported

    @smoke
    Scenario: The experiment can unenroll from the about:studies page
        Given Firefox is launched enrolled in an Experiment
        Then The Experiment is unenrolled via the about:studies page
        And the telemetry shows it as being unenrolled

    @smoke
    Scenario: The experiment can be unenrolled via opting out from studies
        Given Firefox is launched enrolled in an Experiment
        Then The experiment can be unenrolled via opting out of studies
        And the telemetry shows it as being unenrolled
