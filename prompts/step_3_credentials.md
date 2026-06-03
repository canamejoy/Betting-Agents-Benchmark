# Step 3 — Provide Credentials

When the agent has completed implementation and is ready to run the live pipeline,
the user provides credentials directly in the conversation:

```
Here are the credentials:
STAKE_EMAIL=<your-email>
STAKE_PASSWORD=<your-password>
ODDS_API_KEY=<your-key>
TIME_EXPERIMENT=30
```

The agent should write these to `.env` (never commit that file — it is in .gitignore).

After writing `.env`, run the dry-run first:

```
.venv\Scripts\activate
python pipelines/claude/run_live.py
```

Confirm the dry-run output looks correct, then go live:

```
python pipelines/claude/run_live.py --live
```

Type YES at the confirmation prompt.
