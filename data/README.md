# Data

This folder contains datasets used by the benchmark. Both Codex and Claude Code pipelines must use the same files.

## Included Files

- `sample_betting_data.csv` - synthetic dataset with 70 events across soccer, basketball, and tennis from January to March 2024. Use this as the default benchmark dataset.

## Optional Real-Data Files

If you have real betting data, place it here under these names and it will be picked up by the pipelines:

- `historical_odds.csv`
- `historical_results.csv`

Large real-data files such as `historical_*.csv` and `*.parquet` are excluded from version control via `.gitignore`.

## Dataset Schema

```text
event_id,event_date,sport,home_team,away_team,market,selection,odds_decimal,closing_odds_decimal,result
```

The `result` field supports:

- `win`
- `loss`
- `push`

## Synthetic Data Notice

`sample_betting_data.csv` is artificially generated for benchmark purposes only. Results, odds, and team names do not reflect real sporting outcomes. Do not use this data for financial decisions.
