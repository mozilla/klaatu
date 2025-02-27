# Nimbus Integration

This file contains a set of sequence diagrams to describe the integration of Klaatu into the Nimbus project.

## State Diagram

These are the available states and flows that Klaatu can execute. The system follows a structured lifecycle, transitioning between states as experiments are scheduled for testing, testing execution, test result evaluation and test reports are finalized. It starts in an Idle state, waiting for an available experiment or for an experiment to have testing requested on it. Once an experiment is requested, it moves into the Running state, where tests are actively executed. Upon completion, results are processed in the Evaluating state, determining success, failure, or retry conditions. Finally, once results are stored and available in the Experimenter UI, the system transitions back to Idle, ready for the next experiment.

```mermaid
    stateDiagram-v2
        direction LR
        [*] --> Idle

        Idle --> Ready: Experiment Ready for Test
        Ready --> Completed : Job Executes
        Completed --> Ready
        Completed --> [*] : Owner Receives Report

```

## Triggered Run

The Experiment Owner requests a test run. Experimenter gathers the required information and triggers the GitHub Actions Test Runner to execute the tests. The test results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant Experiment Owner
        participant Experimenter Backend
        participant Experimenter UI
        participant Notification System
        participant GitHub Actions Test Runner

        Note over Experimenter Backend: State: IDLE
        Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
        Experimenter UI ->> Experimenter Backend: Test request is forwarded
        Note over Experimenter Backend: State: READY
        Experimenter Backend ->> GitHub Actions Test Runner: Provide Experiment Details
        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Status
        Note over Experimenter Backend: State: RUNNING
        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Note over Experimenter Backend: State: COMPLETED
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experimenter Backend ->> Notification System: Trigger Notification
        Notification System ->> Experiment Owner: Notify Test Completion
        Experiment Owner ->> Experimenter UI: View Test Results & Report

```

## Github Scheduler (Trigger/Test/Report)

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
        GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        Experimenter Backend ->> GitHub Actions Test Runner: Provide Experiment Details
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

## Timeout and No Retry (Trigger/Test/No Retry/Report)

The GitHub Actions Test Runner is triggered to run the tests. The test runner encounters an error and is NOT able to retry the job. The test is marked as a failure and the results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Notification System
        participant Experimenter UI
        participant Experiment Owner

        Note over Experimenter Backend: State: IDLE
        alt Automated Run
            GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        else Manual Run
            Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
            Experimenter UI ->> Experimenter Backend: Test request is forwarded
        end
        Note over Experimenter Backend: State: READY
        Experimenter Backend ->> GitHub Actions Test Runner: Provide Experiment Details
        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Status
        Note over Experimenter Backend: State: RUNNING
        Experimenter Backend ->> GitHub Actions Test Runner: Detect Timeout

        Note over Experimenter Backend: No Retries
        Experimenter Backend ->> Notification System: Send Failure Notification
        Notification System ->> Experiment Owner: Notify Test Error
        Experimenter Backend ->> Experimenter UI: Mark Test as Errored
        Experiment Owner ->> Experimenter UI: View Test Results & Report
        Note over Experimenter Backend: State: READY

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
        alt Automated Run
            GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        else Manual Run
            Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
            Experimenter UI ->> Experimenter Backend: Test request is forwarded
        end
        Note over Experimenter Backend: State: READY
        Experimenter Backend ->> GitHub Actions Test Runner: Provide Experiment Details
        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Status
        Note over Experimenter Backend: State: RUNNING
        Note over GitHub Actions Test Runner: Timeout
        GitHub Actions Test Runner ->> Experimenter Backend: Report Timeout & Request Retry

        Note over Experimenter Backend: Check Retry Count
        Experimenter Backend ->> GitHub Actions Test Runner: Re-trigger Test Execution
        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Note over Experimenter Backend: State: COMPLETED
        Experimenter Backend ->> Notification System: Send Notification
        Notification System ->> Experiment Owner: Notify Test Completion
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experiment Owner ->> Experimenter UI: View Test Results & Report
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
        alt Automated Run
            GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        else Manual Run
            Experiment Owner ->> Experimenter UI: Experiment Owner Requests a Test Run
            Experimenter UI ->> Experimenter Backend: Test request is forwarded
        end
        Note over Experimenter Backend: State: READY
        Experimenter Backend ->> GitHub Actions Test Runner: Start Test Execution
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
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experiment Owner ->> Experimenter UI: View Test Results & Report

```
