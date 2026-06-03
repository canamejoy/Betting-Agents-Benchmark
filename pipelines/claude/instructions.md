# Claude Code-Specific Instructions

Use this file to keep Claude Code runs comparable and auditable.

## Operating Rules

- Work only inside `pipelines/claude/` unless shared benchmark files need a documented update.
- Preserve the shared experiment rules.
- Use explicit commands to run tests and the backtest.
- Record failures instead of hiding them.
- Keep generated reports and metrics in the run folder.

## Prompt Template

```text
You are implementing the Claude Code version of the Betting Agents Benchmark.

Use:
- Shared instructions: ../../instructions/shared_instructions.md
- Experiment: ../../experiments/<experiment_folder>/README.md
- Data: ../../data/

Implement inside pipelines/claude/.
Produce runnable code, tests, metrics.json, and concise run notes.
```
