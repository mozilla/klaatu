# Nimbus Integration

This file contains a set of sequence diagrams to describe the integration of Klaatu into the Nimbus project.

## State Diagram

Klaatu follows a structured lifecycle, transitioning through defined states as experiments progress through testing. The system starts in the IDLE state, waiting for an experiment to be scheduled or requested for testing. Once an experiment is ready, it transitions to the READY state, preparing for execution. When testing begins, the Experiment's testing status moves into the RUNNING state, actively executing tests and collecting results. After execution, the Experiment's testing status transitions to the COMPLETED state, where results are finalized and made available in the Experimenter UI. Once complete, the experiment will remain
in the COMPLETED state if testing has been successful. If the testing has errored in any way, the experiment will be put in a READY state, waiting for the next testing opportunity.

```mermaid
    stateDiagram-v2
        direction LR
        [*] --> Idle

        Idle --> Ready: Experiment Ready for Test
        Ready --> Running : Job Executes
        Running --> Completed: Job Completes
        Running --> Ready: Experiment Ready for Test after timeout or retry
        Completed --> Idle: Experiment Testing cycle restarts
        Completed --> [*] : Owner Receives Report

```

## Github Scheduled Run (Trigger/Test/Report)

The GitHub Actions Scheduler queries the experimenter API and finds experiments to test. It then triggers the GitHub Actions Test Runner to execute the tests. The test results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        
        participant Experiment Owner
        participant Experimenter Backend
        participant Experimenter UI
        participant Notification System
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler

        Note over Experimenter Backend: State: IDLE
        Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
        Experimenter UI ->> Experimenter Backend: Test request is forwarded
        Note over Experimenter Backend: State: READY
        GitHub Actions Scheduler ->> Experimenter Backend: Fetch Available Experiments
        GitHub Actions Scheduler ->> GitHub Actions Test Runner: Provide Experiment Details
        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Status
        Note over Experimenter Backend: State: RUNNING
        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Note over Experimenter Backend: State: COMPLETED
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experimenter Backend ->> Notification System: Trigger Notification
        Notification System ->> Experiment Owner: Notify Test Completion
        Experiment Owner ->> Experimenter UI: View Test Results & Report
```

## Github Scheduler No Available Experiments (Trigger/Query)

The GitHub Actions Scheduler queries the experimenter API and finds experiments to test. There are no available experiments to test.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Notification System
        participant Experimenter UI
        participant Experiment Owner

        Note over Experimenter Backend: State: IDLE
        GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        Note over Experimenter Backend: No Available Experiments
        Note over Experimenter Backend: State: IDLE
```

## Timeout and Retry (Trigger/Test/Timeout/Retry/Report)

The GitHub Actions Test Runner is triggered to run the tests. The test runner encounters a timeout and is able to retry the job. The test results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Notification System
        participant Experimenter UI
        participant Experiment Owner

        Note over Experimenter Backend: State: IDLE
        Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
        Experimenter UI ->> Experimenter Backend: Test request is forwarded
        Note over Experimenter Backend: State: READY
        GitHub Actions Scheduler ->> Experimenter Backend: Fetch Available Experiments
        GitHub Actions Scheduler ->> GitHub Actions Test Runner: Provide Experiment Details
        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Status
        Note over Experimenter Backend: State: RUNNING
        Note over GitHub Actions Test Runner: Timeout
        GitHub Actions Test Runner ->> Experimenter Backend: Report Timeout & Request Retry
        Note over Experimenter Backend: State: READY

```

## Cancelled (Trigger/Cancelled)

The GitHub Actions Test Runner is triggered to run the tests. The job is cancelled by the Experiment Owner while it is being executed. The GitHub Actions Test Runner halts execution and reports a cancellation. The results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Experimenter UI
        participant Notification System
        participant Experiment Owner

        Note over Experimenter Backend: State: IDLE
        Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
        Experimenter UI ->> Experimenter Backend: Test request is forwarded
        Note over Experimenter Backend: State: READY
        GitHub Actions Scheduler ->> GitHub Actions Test Runner: Provide Experiment Details
        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Status
        Note over Experimenter Backend: State: RUNNING
        alt Manually Canceled
            Experiment Owner ->> Experimenter UI: Requests to Cancel Test
            Experimenter UI ->> Experimenter Backend: Forwards test cancellation request
            Experimenter Backend ->> GitHub Actions Test Runner: Cancel Running Test Job
            GitHub Actions Test Runner ->> Experimenter Backend: Report Job Cancellation
        else Infrastructure Failure
            Note over Experimenter Backend: Infrastructure Failure
        end
        Note over Experimenter Backend: State: READY
        Experimenter Backend ->> Notification System: Notify Experiment Owner
        Notification System ->> Experiment Owner: Test Canceled Notification
        Experimenter Backend ->> Experimenter UI: Update UI
        Experiment Owner ->> Experimenter UI: View Test Results & Report

```
