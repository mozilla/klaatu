@adclick_search
Feature: Tests that click ads and verify telemetry

    @smoke
    Scenario: Telemetry reports correctly for URL bar adclick search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something that is likely to return ads
        Then The user clicks on an ad
        And The browser reports correct telemetry for the urlbar adclick event

    @smoke
    Scenario: Telemetry reports correctly for search bar adclick search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something in the search bar that will return ads
        Then The user clicks on an ad
        And The browser reports correct telemetry for the searchbar adclick event

    @smoke
    Scenario: Telemetry reports correctly for context menu adclick search events
        Given Firefox is launched enrolled in an Experiment
        And The user highlights some text and wants to search for it via the context menu
        Then The user clicks on an ad
        And The browser reports correct telemetry for the contextmenu adclick event
