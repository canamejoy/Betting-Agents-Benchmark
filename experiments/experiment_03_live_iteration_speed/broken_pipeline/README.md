# Broken Pipeline - Experiment 03 Starting Point

This folder contains the intentionally broken baseline pipeline used in Experiment 03.

## Setup Instructions

1. Copy `pipeline.py` to `pipelines/<your-tool>/src/pipeline.py`.
2. Do not modify files in this folder.
3. Run the copied pipeline and inspect its behavior.
4. Find and fix the bugs in your copy.
5. Add regression tests in the pipeline folder.

## Benchmark Rule

Both tools must start from this same file and must not receive private hints beyond the public Experiment 03 prompt.

## Expected Deliverables

The corrected tool-specific pipeline should produce:

- Fixed source code in `pipelines/<your-tool>/src/`.
- Tests covering each discovered bug.
- A `metrics.json` file.
- Run notes in `pipelines/<your-tool>/runs/YYYY-MM-DD_experiment_03/`.
