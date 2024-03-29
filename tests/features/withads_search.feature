@with_ads_search
Feature: Search tests that return ads to verify telemetry

    @smoke
    Scenario: Telemetry reports correctly for URL search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        And The browser reports correct telemetry for the urlbar search event

    @smoke
    Scenario: Telemetry reports correctly for search bar search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something in the search bar that will return ads
        And The browser reports correct telemetry for the searchbar search event

    @smoke
    Scenario: Telemetry reports correctly for context menu search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user highlights some text and wants to search for it via the contextmenu

    @smoke
    Scenario: Telemetry reports correctly for new tab search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to search on the new tab
        And The browser reports correct telemetry for the urlbar_handoff search event

    @smoke
    Scenario: Telemetry reports correctly for background search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to perform a background search in the new tab
        And The browser reports correct telemetry for the unknown search event

    @smoke
    Scenario: Telemetry reports correctly for reloaded page search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        And The browser reports correct telemetry for the urlbar search event
        Then The page is refreshed 
        And The browser reports correct telemetry for the reload search event

    @smoke
    Scenario: Telemetry reports correctly for page history search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        And The browser reports correct telemetry for the urlbar search event
        Then The user clicks on an ad
        And The page loads
        Then The user goes back to the search page
        And The browser reports correct telemetry for the tabhistory search event
