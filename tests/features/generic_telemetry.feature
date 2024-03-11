@generic_telemetry
Feature: Generic Telemetry event tests

    @smoke
    Scenario: Report correct telemetry for organic searches
        Given Firefox is launched enrolled in an Experiment
        Then The user searches for something on Google
        And The browser reports correct provider telemetry for the withads organic event
        Then The user clicks on an ad
        And The browser is closed
        Then The browser reports correct provider telemetry for the adclick organic event

    @smoke
    Scenario: Report correct telemetry for tagged searches
        Given Firefox is launched enrolled in an Experiment
        Then The user searches for something that is likely to return ads
        Then The browser reports correct telemetry for the urlbar search event
        Then The user clicks on an ad
        And The browser is closed
        Then The browser reports correct telemetry for the urlbar adclick event

    @smoke
    Scenario: Report correct telemetry for tagged follow on searches
        Given Firefox is launched enrolled in an Experiment
        Then The user searches for something on Google
        And The browser reports correct provider telemetry for the withads organic event
        Then The user triggers a follow-on search
        And The browser is closed
        Then The browser reports correct provider telemetry for the withads unknown tagged follow on event

    @smoke
    Scenario: Report correct telemetry for URI searches
        Given Firefox is launched enrolled in an Experiment
        Then The user searches for something in the search bar that will return ads
        And The browser reports correct telemetry of 1 for the total URI count event
        Then The user searches for something in the search bar that will return ads
        And The browser reports correct telemetry of 2 for the total URI count event

    @smoke
    Scenario: Report correct telemetry for URI normal and private searches
        Given Firefox is launched enrolled in an Experiment
        Then The user searches for something in the search bar that will return ads
        And The browser reports correct telemetry of 1 for the total URI count event
        Then The user searches for something in the search bar that will return ads
        And The browser reports correct telemetry of 2 for the total URI count event

