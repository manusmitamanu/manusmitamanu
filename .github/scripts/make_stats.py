name: update stats

on:
  schedule:
    - cron: "17 0 * * *"   # once a day, 00:17 UTC
  workflow_dispatch:        # the "Run workflow" button

permissions:
  contents: write

concurrency:
  group: stats
  cancel-in-progress: false

jobs:
  stats:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Build stats card
        run: python3 .github/scripts/make_stats.py
        env:
          STATS_TOKEN: ${{ secrets.STATS_TOKEN }}

      - name: Commit updated stats card
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add assets/stats.svg
          if ! git diff --staged --quiet; then
            git commit -m "update stats"
            git pull --rebase
            git push
          fi
