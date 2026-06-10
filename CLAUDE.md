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

Recommended flow (fully Hebrew report):

```bash
python3 market_report.py collect   # runs 12 Tavily searches, saves answers + full article content to /tmp/market-data-YYYY-MM-DD.json
# Claude reads the JSON, runs follow-up searches on the biggest stories, and writes a detailed Hebrew report to /tmp/market-report-YYYY-MM-DD.md
python3 market_report.py search "follow-up query"                # ad-hoc deep search, prints full results
python3 market_report.py send /tmp/market-report-YYYY-MM-DD.md   # ntfy push (plain-text Top 5) + HTML email
```

Legacy one-shot mode (`python3 market_report.py` with no args) still works,
but the body text will contain Tavily's English answers.

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
   1. Run: python3 market_report.py collect
      (saves raw search data — answers + full article content — to
      /tmp/market-data-YYYY-MM-DD.json)
   2. Read the JSON. For the 3–5 biggest / most market-moving stories,
      run follow-up searches to get depth and exact numbers:
      python3 market_report.py search "<focused follow-up query>"
      (e.g. a specific earnings beat, a Fed comment, an Israel-Iran
      development, a big analyst call). Use as many follow-ups as needed.
   3. Write the full report ENTIRELY IN HEBREW — translate everything
      into fluent, natural Hebrew, no English sentences in the body.
      Save it to /tmp/market-report-YYYY-MM-DD.md using the same section
      structure as build_report() in market_report.py.

      Make it DETAILED and analytical, not a summary of summaries.
      For every important item include:
      - **מה קרה:** תיאור קצר וברור עם מספרים מדויקים (%, מחירים, יעדים)
      - **למה זה חשוב:** ההשלכות על השוק
      - **חברות/סקטורים מושפעים**
      - **הזדמנות/סיכון:** מה ניתן לשקול (ללא המלצות קנייה/מכירה)
      - **רמת ביטחון:** 🟢 גבוהה / 🟡 בינונית / 🔴 נמוכה
      - **מקורות:** קישורים למקורות העיקריים
      Be direct and practical; explain logic, data, risks and scenarios.
      If information is missing or unclear — say so explicitly.
   4. Run: python3 market_report.py send /tmp/market-report-YYYY-MM-DD.md
      (sends the plain-text Top 5 push notification and the HTML email)
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
