@adclick_search
Feature: Tests that click ads and verify telemetry

    @smoke
    Scenario: Telemetry reports correctly for URL bar adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        And The user clicks on an ad
        And The browser reports correct telemetry for the urlbar adclick event

    @smoke
    Scenario: Telemetry reports correctly for search bar adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something in the search bar that will return ads
        And The user clicks on an ad
        And The browser reports correct telemetry for the searchbar adclick event

    @smoke
    Scenario: Telemetry reports correctly for context menu adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user highlights some text and wants to search for it via the context menu
        And The user clicks on an ad
        And The browser reports correct telemetry for the contextmenu adclick event


    @smoke
    Scenario: Telemetry reports correctly for new tab adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to search on the new tab
        Then The user clicks on an ad
        And The browser reports correct telemetry for the urlbar_handoff adclick event

    @smoke
    Scenario: Telemetry reports correctly for background adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then Firefox should be allowed to open a new tab
        And The tab should open successfully
        Then The user should be allowed to perform a background search in the new tab
        Then The user clicks on an ad
        And The browser reports correct telemetry for the unknown adclick event

    @smoke
    Scenario: Telemetry reports correctly for reloaded page adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        And The browser reports correct telemetry for the urlbar search event
        Then The page is refreshed
        And The user clicks on an ad
        And The browser reports correct telemetry for the reload adclick event


    @smoke
    Scenario: Telemetry reports correctly for page history adclick search events
        Given Firefox is launched enrolled in an Experiment with custom search
        Then The user searches for something using the nav bar
        And The browser reports correct telemetry for the urlbar search event
        Then The user clicks on an ad
        And The page loads
        Then The user goes back to the search page
        Then The user clicks on an ad
        Then The browser reports correct telemetry for the tabhistory adclick event
