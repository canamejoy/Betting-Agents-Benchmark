# Experiment 03: Live Iteration Speed

## Purpose

Measure each tool's ability to debug and improve an existing betting pipeline under time pressure.

## Task Prompt

Given a partially working betting-agent pipeline with one or more failing tests or metric issues, diagnose the problem, fix it, rerun tests, and improve reporting without changing the benchmark rules.

## Setup

Use `broken_pipeline/pipeline.py` as the same broken starting point for both tools.

Do not provide private bug inventories, answer keys, or targeted hints to either tool. The experiment measures debugging behavior, so both tools should discover the issues from code review, tests, and observed outputs.

Keep any organizer-only answer key outside this repository, or in a path ignored by `.gitignore`, before giving either tool access to the benchmark tree.

## Required Behavior

- Identify the bugs.
- Fix the implementation.
- Add or update tests.
- Rerun the benchmark.
- Explain the cause and fix.

## Suggested Acceptance Criteria

- Tests pass.
- The fixed metrics are mathematically correct.
- The fix does not remove benchmark requirements.
- The explanation is specific and concise.

## Primary Metrics

- Debug recovery time.
- Iterations to pass tests.
- Correctness of fix.
- Regression test quality.
- Final runtime.
