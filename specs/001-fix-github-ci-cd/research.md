# Research: Fix GitHub CI/CD Pipeline

## 1. Investigate Failing `nightly-tests`

**Task:** "Investigate the root cause of the `nightly-tests` job failure."

**Findings:**

*   **Decision:** The `nightly-tests` job is failing due to a coverage check failure.
*   **Rationale:** When running `pytest --cov=jafgen --cov-report=xml`, the tests pass, but the coverage check fails. The required coverage is 85%, but the actual coverage is much lower when only running a subset of tests. The fix is to ensure that all tests are run in the nightly job to meet the coverage requirement.
*   **Alternatives considered:** Lowering the coverage requirement, but this is not recommended as it would reduce code quality.

## 2. Performance Goals, Constraints, and Scale/Scope

**Task:** "Clarify Performance Goals, Constraints, and Scale/Scope."

**Findings:**

*   **Decision:** These are not critical for fixing the CI/CD pipeline and will be deferred.
*   **Rationale:** The immediate goal is to unblock the CI/CD pipeline. Performance, constraints, and scale are not relevant to this task.
*   **Alternatives considered:** None.
