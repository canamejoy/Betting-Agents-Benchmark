# Experiment 03 Prompt - Live Iteration Speed

Copy this prompt verbatim when starting the experiment with each tool.

---

You are debugging and fixing a broken betting-agent pipeline for the Betting Agents Benchmark.

Read these files before writing any code:
- Shared rules: `instructions/shared_instructions.md`
- Experiment spec: `experiments/experiment_03_live_iteration_speed/README.md`
- Broken starting point: `experiments/experiment_03_live_iteration_speed/broken_pipeline/pipeline.py`
- Dataset: `data/sample_betting_data.csv`

Copy `broken_pipeline/pipeline.py` into `pipelines/<your-tool>/src/` as your starting point. Do not modify the broken_pipeline folder.

## Task

The pipeline has several bugs. Find and fix all of them, add tests, and produce a correct benchmark run.

Your job:
1. Run the pipeline and observe failures or incorrect outputs.
2. Identify each bug and explain it.
3. Fix the implementation.
4. Add or update tests so each bug is covered by a regression test.
5. Rerun the pipeline and confirm correct outputs.
6. Document your process.

## Constraints

- Do not change the benchmark evaluation rules or loosen acceptance criteria to make tests pass.
- Do not delete failing tests; fix the implementation instead.
- Explain each bug cause and fix in `runs/YYYY-MM-DD_experiment_03/notes.md`.

## Deliverables

- Fixed source code in `pipelines/<your-tool>/src/`
- Updated tests with regression coverage for each bug
- `metrics.json` with correct outputs
- `runs/YYYY-MM-DD_experiment_03/notes.md` with: each bug found, root cause, fix applied, and time spent per bug
