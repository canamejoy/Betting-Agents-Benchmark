# Quickstart — Running the Benchmark

## Branch Structure

| Branch | Purpose |
|--------|---------|
| `main` | Shared base: experiments, instructions, data, metrics |
| `claude-run` | Claude Code's implementation |
| `codex-run` | Codex's implementation |

Each agent works only inside its own branch. The shared files in `experiments/`, `instructions/`, `data/`, and `metrics/` are the same on all branches.

---

## How to Start a New Agent Run

Use these 3 prompts **in order** at the start of each session.

### Step 1 — Read and Analyze (no code changes)

Copy the contents of [`prompts/step_1_read.md`](prompts/step_1_read.md) and send it to the agent.

> Read the entire repository.
> Read all documentation files.
> Summarize: project objective, architecture, pending tasks, implementation strategy.
> Do not modify any files yet.

Wait for the agent to summarize the repo before continuing.

---

### Step 2 — Proceed with Implementation

Copy the contents of [`prompts/step_2_implement.md`](prompts/step_2_implement.md) and send it to the agent.

> Proceed with implementation. You have my authorization to use my Stake account per the repository instructions.
> You may: create files, modify files, run tests, install dependencies.
> Keep changes within this repository only.
> Document major decisions.

The agent will implement the pipeline and tell you when it is ready for credentials.

---

### Step 3 — Provide Credentials

Once the agent is ready, provide the credentials in the conversation:

```
Here are the credentials:
STAKE_EMAIL=your_email
STAKE_PASSWORD=your_password
ODDS_API_KEY=your_key
```

See [`prompts/step_3_credentials.md`](prompts/step_3_credentials.md) for the full instructions.

---

## Setup (one-time)

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium
```

## Running the Live Pipeline

```powershell
# Dry-run (no real bets placed — recommended first)
python pipelines/claude/run_live.py

# Live mode — places real bets on Stake.com
python pipelines/claude/run_live.py --live
```

Output is saved to `pipelines/claude/runs/live/live_report.json`.

---

## Running the Backtest Experiments

```powershell
python pipelines/claude/run_experiment_01.py   # Baseline
python pipelines/claude/run_experiment_02.py   # Risk-aware bankroll
python pipelines/claude/run_experiment_03.py   # Iteration speed
```

---

## Switching Branches

```powershell
# Claude Code's branch
git checkout claude-run

# Codex's branch
git checkout codex-run
```
