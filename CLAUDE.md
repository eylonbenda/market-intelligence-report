# Market Intelligence Report — Daily Automation

## What this repo does

Runs a daily Hebrew market intelligence report covering:
- US markets (S&P 500, Nasdaq, Dow)
- Israeli market (TA-35, shekel/USD)
- Semiconductors & AI (Nvidia, AMD, Intel)
- Fed / Bank of Israel / macro
- Crypto (BTC, ETH)
- Earnings, analyst upgrades, ETF flows
- Israel-Iran geopolitics & oil

## How to run

```bash
python3 market_report.py
```

The script:
1. Runs 12 Tavily searches
2. Builds a Hebrew Markdown report
3. Saves to `/tmp/market-report-YYYY-MM-DD.md`
4. Sends a push notification via ntfy.sh (Top 5 section)
5. Emails the full HTML report via Resend

## Required environment variables

Set these in the Claude Code environment settings (☁️ Default → gear icon → Environment variables):

| Variable | Description | Example |
|----------|-------------|---------|
| `TAVILY_API_KEY` | Tavily search API key | `tvly-dev-...` |
| `NTFY_TOPIC` | ntfy.sh topic name | `market-report-eylon` |
| `RESEND_API_KEY` | Resend email API key | `re_...` |
| `REPORT_EMAIL` | Recipient email address | `you@gmail.com` |
| `REPORT_EMAIL_FROM` | Sender address (verified domain) | `market@yourdomain.com` |

## Required network access

The environment must have **Full** or **Custom** network access with these domains allowed:
- `api.tavily.com` — search
- `ntfy.sh` — push notification
- `api.resend.com` — email delivery

## Setting up the daily Routine

In Claude Code on the web:
1. Go to **Routines** in the left sidebar
2. Create a new routine: **"Daily Market Report"**
3. Trigger: every day at your preferred time (e.g. 07:00)
4. Repo: `eylonbenda/market-intelligence-report`
5. Prompt:
   ```
   Run the daily market intelligence report:
   python3 market_report.py
   ```

## Getting a Resend API key (free email)

1. Sign up at [resend.com](https://resend.com) — free tier sends 100 emails/day
2. Add and verify your domain (or use `onboarding@resend.dev` for testing)
3. Create an API key under Settings → API Keys
4. Paste it as `RESEND_API_KEY` in the environment variables

## Getting an ntfy.sh notification on iPhone

1. Install the **ntfy** app from the App Store
2. Subscribe to topic: `market-report-eylon` (or change `NTFY_TOPIC`)
3. That's it — no account required for public topics
