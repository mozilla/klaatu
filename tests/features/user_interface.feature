@user_flow
Feature: User Interactions with Firefox are not hindered

    @smoke
    Scenario: The browser can navigate effectively
        Given Firefox is launched enrolled in an Experiment
        When The user navigates to a webpage
        Then Firefox should load the webpage

    @smoke
    Scenario: The experiment does not drastically slow down Firefox
        Given Firefox is launched enrolled in an Experiment
        Then Firefox should not be slowed down

    @smoke
    Scenario: The experiment shows on the studies page
        Given Firefox is launched enrolled in an Experiment
        Then The Experiment should be shown on the about:studies page

    @smoke
    Scenario: The experiment shows on the support page
        Given Firefox is launched enrolled in an Experiment
        Then The Experiment should be shown on the about:support page

    @smoke
    Scenario: The experiment should not block Firefox updates
        Given Firefox is launched enrolled in an Experiment
        Then A user chooses to update Firefox
        Then Firefox updates correctly
        And The experiment is still enrolled