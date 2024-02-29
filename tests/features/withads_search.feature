@with_ads_search
Feature: Search tests that return ads to verify telemetry

    @smoke
    Scenario: Telemetry reports correctly for URL search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something that is likely to return ads
        Then The browser reports correct telemetry for the urlbar search event

    @smoke
    Scenario: Telemetry reports correctly for search bar search events
        Given Firefox is launched enrolled in an Experiment
        And The user searches for something in the search bar that will return ads
        Then The browser reports correct telemetry for the searchbar search event

    @smoke
    Scenario: Telemetry reports correctly for context menu search events
        Given Firefox is launched enrolled in an Experiment
        And The user highlights some text and wants to search for it via the context menu
        Then The browser reports correct telemetry for the contextmenu search event

    @smoke
    Scenario: Telemetry reports correctly for new tab search events
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to search on the new tab
        And The browser reports correct telemetry for the urlbar_handoff search event

    @smoke
    Scenario: Telemetry reports correctly for background search events
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to perform a background search in the new tab
        And The browser reports correct telemetry for the unknown search event
