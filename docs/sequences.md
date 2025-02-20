# Nimbus Integration

This file contains a set of sequence diagrams to describe the integration of Klaatu into the Nimbus project.

## State Diagram

These are the available states and flows that Klaatu can execute. The system follows a structured lifecycle, transitioning between states as experiments are scheduled for testing, testing execution, test result evaluation and test reports are finalized. It starts in an Idle state, waiting for an available experiment or for an experiment to have testing requested on it. Once an experiment is requested, it moves into the Running state, where tests are actively executed. Upon completion, results are processed in the Evaluating state, determining success, failure, or retry conditions. Finally, once results are stored and available in the Experimenter UI, the system transitions back to Idle, ready for the next experiment.

```mermaid
    stateDiagram-v2
        direction LR
        [*] --> Idle

        Idle --> Running: Experiment Ready for Test
        Running --> Completed : Job Executes
        Completed --> Running: Job Retries
        Completed --> Evaluate : Send Results
        Evaluate --> [*] : Owner Receives Report
        Evaluate --> Idle

```

## Triggered Run

The Experiment Owner requests a test run. Experimenter gathers the required information and triggers the GitHub Actions Test Runner to execute the tests. The test results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant Experimenter Backend
        participant Experimenter Worker
        participant Experimenter UI
        participant Notification System
        participant Experiment Owner

        Note left of Experiment Owner: State: IDLE
        Experiment Owner ->> Experimenter Backend: Experiment Owner Requests a Test Run
        Experimenter Backend ->> GitHub Actions Test Runner: Provide Experiment Details
        Note right of GitHub Actions Test Runner: State: RUNNING
        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Note right of GitHub Actions Test Runner: State: COMPLETED
        Experimenter Backend ->> Experimenter Worker: Process Results
        Note right of Experimenter Backend: State: EVALUATE
        Experimenter Backend ->> Notification System: Send Notification
        Notification System ->> Experiment Owner: Notify Test Completion
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experimenter UI ->> Experiment Owner: Show Test Results & Report
        Note right of Experimenter UI: State: IDLE
```

## Github Scheduler (Trigger/Test/Report)

The GitHub Actions Scheduler queries the experimenter API and finds experiments to test. It then triggers the GitHub Actions Test Runner to execute the tests. The test results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Experimenter Worker
        participant Experimenter UI
        participant Notification System
        participant Experiment Owner

        Note right of GitHub Actions Scheduler: State: IDLE
        GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        Experimenter Backend ->> GitHub Actions Scheduler: Provide Experiment Details
        GitHub Actions Scheduler ->> GitHub Actions Test Runner: Start Test Execution
        Note right of GitHub Actions Test Runner: State: RUNNING
        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Note right of GitHub Actions Test Runner: State: COMPLETED
        Experimenter Backend ->> Experimenter Worker: Process Results
        Note right of Experimenter Backend: State: EVALUATE
        Experimenter Backend ->> Notification System: Send Notification
        Notification System ->> Experiment Owner: Notify Test Completion
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experimenter UI ->> Experiment Owner: Show Test Results & Report
        Note right of Experimenter UI: State: IDLE
```

## Github Scheduler No Available Experiments (Trigger/Query)

The GitHub Actions Scheduler queries the experimenter API and finds experiments to test. There are no available experiments to test.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Experimenter Worker
        participant Experimenter UI
        participant Notification System
        participant Experiment Owner

        Note right of GitHub Actions Scheduler: State: IDLE
        GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        Note right of GitHub Actions Scheduler: State: RUNNING
        Note over Experimenter Backend: No Available Experiments
        Note right of GitHub Actions Scheduler: State: IDLE
```

## Timeout and No Retry (Trigger/Test/No Retry/Report)

The GitHub Actions Test Runner is triggered to run the tests. The test runner encounters an error and is NOT able to retry the job. The test is marked as a failure and the results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Experimenter Worker
        participant Experimenter UI
        participant Notification System
        participant Experiment Owner


        alt Automated Run
            Note right of GitHub Actions Scheduler: State: IDLE
            GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        else Manual Run
            Note left of Experiment Owner: State: IDLE
            Experiment Owner ->> Experimenter Backend: Experiment Owner Requests a Test Run
        end
        Experimenter Backend ->> GitHub Actions Scheduler: Provide Experiment Details
        GitHub Actions Scheduler ->> GitHub Actions Test Runner: Start Test Execution
        Note right of GitHub Actions Test Runner: State: RUNNING
        Experimenter Backend ->> GitHub Actions Test Runner: Detect Timeout
        GitHub Actions Test Runner ->> Experimenter Backend: Report Timeout & Request Retry
        Note right of GitHub Actions Test Runner: State: COMPLETED

        Note over Experimenter Backend: No Retries
        Experimenter Backend ->> Experimenter Worker: Mark Test as Failed
        Note right of Experimenter Backend: State: EVALUATE
        Experimenter Backend ->> Notification System: Send Failure Notification
        Notification System ->> Experiment Owner: Notify Test Failure
        Note right of Notification System: State: IDLE

```

## Timeout and Retry (Trigger/Test/Timeout/Retry/Report)

The GitHub Actions Test Runner is triggered to run the tests. The test runner encounters a timeout and is able to retry the job. The test results are pushed to Experimenter where they are processed and then provided to the UI. Experimenter also sends a notification to the Experiment Owner of the test results.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant GitHub Actions Scheduler
        participant Experimenter Backend
        participant Experimenter Worker
        participant Experimenter UI
        participant Notification System
        participant Experiment Owner


        alt Automated Run
            Note right of GitHub Actions Scheduler: State: IDLE
            GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        else Manual Run
            Note left of Experiment Owner: State: IDLE
            Experiment Owner ->> Experimenter Backend: Experiment Owner Requests a Test Run
        end
        Experimenter Backend ->> GitHub Actions Scheduler: Provide Experiment Details
        GitHub Actions Scheduler ->> GitHub Actions Test Runner: Start Test Execution
        Note right of GitHub Actions Test Runner: State: RUNNING
        Note over GitHub Actions Test Runner: Timeout
        GitHub Actions Test Runner ->> Experimenter Backend: Report Timeout & Request Retry

        Note over Experimenter Backend: Check Retry Count
        Experimenter Backend ->> GitHub Actions Test Runner: Re-trigger Test Execution
        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Note right of GitHub Actions Test Runner: State: COMPLETED
        Experimenter Backend ->> Experimenter Worker: Process Results
        Note right of Experimenter Backend: State: EVALUATE
        Experimenter Backend ->> Notification System: Send Notification
        Notification System ->> Experiment Owner: Notify Test Completion
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experimenter UI ->> Experiment Owner: Show Test Results & Report
        Note right of Experimenter UI: State: IDLE
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

        alt Automated Run
            Note right of GitHub Actions Scheduler: State: IDLE
            GitHub Actions Scheduler ->> Experimenter Backend: Check for Available Experiments
        else Manual Run
            Note left of Experiment Owner: State: IDLE
            Experiment Owner ->> Experimenter Backend: Experiment Owner Requests a Test Run
        end
        Experimenter Backend ->> GitHub Actions Test Runner: Start Test Execution
        Note right of GitHub Actions Test Runner: State: RUNNING
        alt Manually Canceled
            Experiment Owner ->> GitHub Actions Test Runner: Cancel Running Test Job
        else Infrastructure Failure
            Note right of GitHub Actions Test Runner: Infrastructure Failure
        end

        GitHub Actions Test Runner ->> Experimenter Backend: Report Job Cancellation
        Note right of GitHub Actions Test Runner: State: COMPLETED

        Experimenter Backend ->> Experimenter UI: Process Results
        Note right of Experimenter Backend: State: EVALUATE
        Experimenter Backend ->> Notification System: Notify Experiment Owner
        Notification System ->> Experiment Owner: Test Canceled Notification
        Experimenter Backend ->> Experimenter UI: Store Report & Update UI
        Experimenter UI ->> Experiment Owner: Show Test Results & Report
        Note right of Experimenter UI: State: IDLE

```

## Experimenter results processing error

The test results are pushed to Experimenter where they are processed. If they are processed successfully the results are pushed to the UI. If there is an error, the Experimenter Worker tries again. If the retry fails as well the test is marked as an Infrastructure fail and provided to the UI. Experimenter also sends a notification to the Experiment Owner.

```mermaid
    sequenceDiagram
        participant GitHub Actions Test Runner
        participant Experimenter Backend
        participant Experimenter Worker
        participant Notification System

        Note right of GitHub Actions Test Runner: State: COMPLETED

        GitHub Actions Test Runner ->> Experimenter Backend: Report Test Results
        Experimenter Backend ->> Experimenter Worker: Process Results
        Note right of Experimenter Backend: State: EVALUATE

        alt Worker Fails
            Experimenter Worker ->> Experimenter Backend: Error Processing Results
            Experimenter Backend ->> Experimenter Worker: Retry Processing
            alt Retry Succeeds
                Experimenter Backend ->> Notification System: Send Notification
                Experimenter Backend ->> Experimenter UI: Store Report & Update UI
                Experimenter UI ->> Experiment Owner: Show Test Results & Report
                Note right of Experimenter UI: State: IDLE
            else Retry Fails
                Experimenter Backend ->> Notification System: Send Failure Notification
                Note over Notification System: Infrastructure fail
                Notification System ->> Experiment Owner: Notify Backend Failure
                Note right of Notification System: State: IDLE
            end
        end

```
