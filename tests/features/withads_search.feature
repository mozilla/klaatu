@with_ads_search
Feature: Search tests that return ads to verify telemetry

    @smoke
    Scenario: Telemetry reports correctly for URL search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something that is likely to return ads
        Then The browser reports correct telemetry for the search event

    @smoke
    Scenario: Telemetry reports correctly for search bar search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something in the search bar that will return ads
        Then The browser reports correct telemetry for the searchbar event
