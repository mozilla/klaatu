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


    @smoke
    Scenario: Telemetry reports correctly for new tab adclick search events
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to search on the new tab
        Then The user clicks on an ad
        And The browser reports correct telemetry for the urlbar_handoff adclick event

    @smoke
    Scenario: Telemetry reports correctly for background adclick search events
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to perform a background search in the new tab
        Then The user clicks on an ad
        And The browser reports correct telemetry for the unknown adclick event

    @smoke
    Scenario: Telemetry reports correctly for reloaded page adclick search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something that is likely to return ads
        Then The browser reports correct telemetry for the urlbar search event
        Then The page is refreshed
        And The user clicks on an ad
        Then The browser is closed
        And The browser reports correct telemetry for the reload adclick event
