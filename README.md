# 132lilinwei.github.io

## Daily arXiv email app (LLM focus)

This repo now includes an automated app that:

- Queries arXiv every day for new papers related to:
  - text LLMs
  - pretraining
  - post-training
  - reinforcement learning (including RLHF/alignment)
- Sends a daily digest email to `linweili@gmail.com`.

### Files

- `scripts/arxiv_digest.py`: fetches papers from arXiv and sends an email.
- `.github/workflows/daily-arxiv-email.yml`: runs the script once per day with GitHub Actions.

### Setup (GitHub)

1. Go to your GitHub repo: **Settings → Secrets and variables → Actions**.
2. Add these repository secrets:
   - `SMTP_HOST` (example: `smtp.gmail.com`)
   - `SMTP_PORT` (example: `465`)
   - `SMTP_USER` (your sender Gmail address)
   - `SMTP_PASSWORD` (Gmail app password)
3. Push this repo to GitHub.
4. Open **Actions** tab and run **Daily arXiv Email Digest** once with `workflow_dispatch` to test.
5. After that, it runs automatically every day.

### Notes

- Recipient is set to `linweili@gmail.com` in workflow env.
- You can tune search scope with `ARXIV_QUERY`, `ARXIV_MAX_RESULTS`, and `ARXIV_LOOKBACK_DAYS`.
- For Gmail, use an app password (not your normal login password).
