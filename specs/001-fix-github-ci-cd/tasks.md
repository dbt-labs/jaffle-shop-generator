# Feature Tasks: Fix GitHub CI/CD Pipeline

**Feature**: `001-fix-github-ci-cd`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

This document outlines the tasks required to implement the "Fix GitHub CI/CD Pipeline" feature.

## Phase 1: Setup

There are no specific setup tasks for this feature.

## Phase 2: Foundational Tasks

There are no foundational tasks required for this feature.

## Phase 3: User Story 1 - CI/CD Pipeline Success

### Story Goal
As a developer, I want the CI/CD pipeline to run successfully on every commit and pull request, so that I can get fast feedback on my changes and ensure the codebase is always in a deployable state.

### Independent Test Criteria
A developer can push a commit to a branch with an open pull request and see the "all checks have passed" green checkmark on GitHub.

### Implementation Tasks
- [x] T001 [US1] Review `.github/workflows/nightly.yml` to confirm that the `pytest` command is correctly configured to run all tests and generate a coverage report. The command should be `pytest --cov=jafgen --cov-report=xml`.
- [x] T002 [US1] Run the test suite locally using the same command as the CI job (`pytest --cov=jafgen --cov-report=xml`) to reproduce the failure and confirm that the coverage check is the root cause.
- [x] T003 [US1] Analyze the coverage report to identify untested code paths.
- [x] T004 [US1] Write additional tests for the untested code paths to increase code coverage above the 85% threshold.
- [x] T005 [US1] Re-run the test suite with coverage to confirm that the coverage check now passes.
- [ ] T006 [US1] Commit the changes to the `001-fix-github-ci-cd` branch.
- [ ] T007 [US1] Push the changes to the remote repository and open a pull request to merge into `main`.

## Dependencies

- **US1** is independent and can be worked on immediately.

## Parallel Execution

All tasks within User Story 1 are sequential and should be executed in order. There are no parallel execution opportunities.

## Implementation Strategy

The strategy is to fix the immediate cause of the CI/CD pipeline failure, which is the test coverage check. The tasks are ordered to first confirm the issue, then address it by adding more tests, and finally verify the fix before merging.
