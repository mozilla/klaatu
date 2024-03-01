@adclick_search
Feature: Tests that click ads and verify telemetry

    @smoke
    Scenario: Telemetry reports correctly for URL bar adclick search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something that is likely to return ads
        Then The user clicks on an ad
        And The browser reports correct telemetry for the urlbar adclick event
