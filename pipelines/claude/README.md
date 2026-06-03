# Claude Code Pipeline

This folder contains the Claude Code implementation and run artifacts for the betting-agent benchmark.

## Intended Contents

```text
pipelines/claude/
├── README.md
├── instructions.md
├── architecture.md
├── runs/
└── src/
```

## How To Use

1. Give Claude Code the shared instructions from `../../instructions/shared_instructions.md`.
2. Give Claude Code the selected experiment prompt from `../../experiments/`.
3. Ask Claude Code to implement the pipeline in this folder.
4. Record run notes in `runs/`.
5. Score the result with `../../metrics/scorecard_template.csv`.

## Expected Claude Code Outputs

- Runnable source code.
- Tests for EV, ROI, stake sizing, and leakage controls.
- `metrics.json` for each run.
- Short notes describing assumptions, commands, failures, and fixes.

## Suggested Run Record

For each run, create:

```text
runs/YYYY-MM-DD_experiment_name/
├── prompt.md
├── commands.md
├── metrics.json
├── notes.md
└── artifacts/
```
