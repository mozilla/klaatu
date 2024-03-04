@generic_telemetry
Feature: Generic Telemetry event tests

    @smoke
    Scenario: Report correct telemetry for organic searches
        Given Firefox is launched enrolled in an Experiment
        Then The user searches for something on Google
        And The user clicks on an ad
        Then The browser reports correct provider telemetry for the adclick organic event
        And The browser reports correct provider telemetry for the withads organic event