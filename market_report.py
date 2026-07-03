#!/usr/bin/env python3
"""
Daily market intelligence report — Hebrew
Requires env vars: TAVILY_API_KEY, NTFY_TOPIC, RESEND_API_KEY, REPORT_EMAIL
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date

# ── Config ─────────────────────────────────────────────────────────────────
TODAY       = date.today().strftime("%Y-%m-%d")
REPORT_PATH = f"/tmp/market-report-{TODAY}.md"

DATA_PATH   = f"/tmp/market-data-{TODAY}.json"

TAVILY_KEY  = os.environ.get("TAVILY_API_KEY", "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")
NTFY_TOPIC  = os.environ.get("NTFY_TOPIC", "market-report-eylon")
RESEND_KEY  = os.environ.get("RESEND_API_KEY", "")
EMAIL_TO    = os.environ.get("REPORT_EMAIL", "eylonbd6@gmail.com")
EMAIL_FROM  = os.environ.get("REPORT_EMAIL_FROM", "onboarding@resend.dev")  # use your verified domain once set up

# Resend/ntfy sit behind Cloudflare, which bot-blocks the default urllib
# User-Agent (HTTP 403 "error code: 1010"). Send a browser-like UA.
USER_AGENT  = "Mozilla/5.0 (market-report-bot)"


# ── Helpers ─────────────────────────────────────────────────────────────────

def tavily_search(query: str, max_results: int = 8) -> dict:
    payload = json.dumps({
        "api_key": TAVILY_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "include_raw_content": True,
        "max_results": max_results,
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [Tavily] WARN: {query[:50]} → {e}", file=sys.stderr)
        return {}


def send_ntfy(title: str, message: str) -> bool:
    payload = json.dumps({
        "title": title,
        "message": message,
        "priority": 3,
        "tags": ["chart_with_upwards_trend"],
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"  [ntfy] Sent — HTTP {r.status}")
            return True
    except Exception as e:
        print(f"  [ntfy] ERROR: {e}", file=sys.stderr)
        return False


def send_email(subject: str, html_body: str) -> bool:
    if not RESEND_KEY:
        print("  [email] WARN: RESEND_API_KEY not set — skipping email", file=sys.stderr)
        return False
    payload = json.dumps({
        "from": EMAIL_FROM,
        "to": [EMAIL_TO],
        "subject": subject,
        "html": html_body,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RESEND_KEY}",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            print(f"  [email] Sent to {EMAIL_TO} — id={resp.get('id')}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [email] ERROR HTTP {e.code}: {body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  [email] ERROR: {e}", file=sys.stderr)
        return False


def md_to_html(md: str) -> str:
    """Minimal markdown→HTML for email readability."""
    import re
    lines = md.splitlines()
    html_lines = []
    in_table = False
    for line in lines:
        # Table rows
        if line.startswith("|"):
            if not in_table:
                html_lines.append("<table border='1' cellpadding='6' style='border-collapse:collapse;font-size:13px'>")
                in_table = True
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if "---" not in line else None
            if tag is None:
                continue
            html_lines.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            continue
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False
        # Headers
        if line.startswith("# "):
            html_lines.append(f"<h1 style='color:#1a237e'>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2 style='color:#283593;border-bottom:2px solid #e8eaf6;padding-bottom:4px'>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3 style='color:#3949ab'>{line[4:]}</h3>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<p><strong>{line[2:-2]}</strong></p>")
        elif line.startswith("> "):
            html_lines.append(f"<blockquote style='color:#555;border-left:3px solid #9fa8da;padding-left:10px'>{line[2:]}</blockquote>")
        elif re.match(r"^\d+\. ", line):
            html_lines.append(f"<li>{line[line.index(' ')+1:]}</li>")
        elif line.startswith("- ") or line.startswith("* "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("---"):
            html_lines.append("<hr style='border:1px solid #e8eaf6'>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            # Bold inline
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            # Links
            line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', line)
            html_lines.append(f"<p style='margin:4px 0'>{line}</p>")
    if in_table:
        html_lines.append("</table>")
    return f"""
    <html><body style='font-family:Arial,sans-serif;max-width:900px;margin:auto;padding:20px;
    background:#f5f5f5;color:#212121;direction:rtl;text-align:right'>
    {''.join(html_lines)}
    <hr><p style='font-size:11px;color:#999'>דוח אוטומטי — {TODAY} | אין ייעוץ השקעות</p>
    </body></html>
    """


# ── Search queries ──────────────────────────────────────────────────────────

QUERIES = [
    f"S&P 500 Nasdaq Dow Jones market movement {TODAY}",
    f"Israel TASE Tel Aviv 35 stock market news {TODAY}",
    f"Nvidia AMD Intel semiconductor chip stocks news {TODAY}",
    f"Federal Reserve interest rate inflation CPI news {TODAY}",
    f"Bitcoin Ethereum cryptocurrency price {TODAY}",
    f"Earnings reports results this week {TODAY}",
    f"Bank of Israel interest rate shekel USD ILS news {TODAY}",
    f"Israel Iran geopolitical oil prices news {TODAY}",
    f"Wall Street analyst upgrades downgrades price targets {TODAY}",
    f"AI artificial intelligence tech companies news {TODAY}",
    f"Oil energy Brent WTI commodities {TODAY}",
    f"Hot investment trends sectors ETF flows {TODAY}",
]


# ── Report generation ───────────────────────────────────────────────────────

def build_report(results: list[dict]) -> str:
    def ans(i): return results[i].get("answer", "אין מידע זמין")
    def srcs(i):
        return " | ".join(
            f"[{r.get('title','')[:40]}]({r.get('url','')})"
            for r in results[i].get("results", [])[:3]
        )

    us_mkt   = ans(0);  us_src   = srcs(0)
    il_mkt   = ans(1);  il_src   = srcs(1)
    chips    = ans(2);  chips_src= srcs(2)
    fed      = ans(3);  fed_src  = srcs(3)
    crypto   = ans(4);  crypto_src=srcs(4)
    earn     = ans(5);  earn_src = srcs(5)
    boi      = ans(6);  boi_src  = srcs(6)
    geo      = ans(7);  geo_src  = srcs(7)
    analyst  = ans(8);  analyst_src=srcs(8)
    ai_tech  = ans(9);  ai_src   = srcs(9)
    oil      = ans(10); oil_src  = srcs(10)
    etf      = ans(11); etf_src  = srcs(11)

    return f"""# 📊 דוח מודיעין שוקי ההון — {TODAY}

> נערך אוטומטית | תאריך: {TODAY} | שפה: עברית | אין המלצת השקעה — ניתוח, נתונים ותרחישים בלבד

---

## 🔥 5 הדברים החשובים ביותר לצפייה היום

1. **שוקי ארה"ב** — {us_mkt[:200]}
2. **גיאופוליטיקה ונפט** — {geo[:200]}
3. **שבבים ו-AI** — {chips[:200]}
4. **ריבית ואינפלציה** — {fed[:200]}
5. **קריפטו** — {crypto[:200]}

---

## 🌍 שוקי ההון הגלובליים

{us_mkt}

**מקורות:** {us_src}

---

## 🇮🇱 שוק ישראלי — בורסת תל אביב

{il_mkt}

**מקורות:** {il_src}

---

## 📈 דוחות רווחים ועדכוני חברות

{earn}

**מקורות:** {earn_src}

---

## 🚀 טרנדים ומגמות חמות

{etf}

**מקורות:** {etf_src}

---

## 🤖 AI, שבבים, פינטק ואנרגיה

### שבבים — Nvidia / AMD / Intel

{chips}

**מקורות:** {chips_src}

### AI ו-Tech

{ai_tech}

**מקורות:** {ai_src}

---

## 🌐 מאקרו, ריבית וגיאופוליטיקה

### הפד — ריבית ואינפלציה

{fed}

**מקורות:** {fed_src}

### בנק ישראל

{boi}

**מקורות:** {boi_src}

### ישראל-איראן וגיאופוליטיקה

{geo}

**מקורות:** {geo_src}

---

## 💹 קריפטו

{crypto}

**מקורות:** {crypto_src}

---

## 📊 עדכוני אנליסטים ופעילות מוסדית

{analyst}

**מקורות:** {analyst_src}

---

## ⚠️ אנרגיה, סחורות וסיכונים

{oil}

**מקורות:** {oil_src}

---

## 🔭 מה לצפות בימים הקרובים

- עקוב אחר ישיבות הפד / בנק ישראל הקרובות
- דוחות רווח מרכזיים השבוע: {earn[:150]}
- מעקב אחר מחיר הנפט ומצב הורמוז
- עדכוני AI / שבבים מאנליסטים

---

*דוח זה נערך אוטומטית לצרכי מידע בלבד. אין בו ייעוץ השקעות.*
"""


# ── Sub-commands ─────────────────────────────────────────────────────────────

def cmd_collect():
    """Run all 12 searches and dump raw data (answers + full content) to JSON."""
    print(f"[collect] Running {len(QUERIES)} Tavily searches — {TODAY}")
    results = []
    for i, q in enumerate(QUERIES, 1):
        print(f"  [{i:02d}/{len(QUERIES)}] {q[:60]}")
        results.append({"query": q, "data": tavily_search(q)})
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[collect] Raw data saved → {DATA_PATH}")


def cmd_search(query: str):
    """Run a single focused follow-up search and print the answer + sources."""
    print(f"[search] {query}", file=sys.stderr)
    data = tavily_search(query)
    print(json.dumps({
        "query": query,
        "answer": data.get("answer", ""),
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "raw_content": (r.get("raw_content") or "")[:4000],
            }
            for r in data.get("results", [])
        ],
    }, ensure_ascii=False, indent=2))


def cmd_send(path: str):
    """Read a finished Markdown report, push Top-5 via ntfy, email full HTML."""
    with open(path, "r", encoding="utf-8") as f:
        report = f.read()

    # Extract the Top-5 section for the push notification.
    marker = "## 🔥 5 הדברים החשובים ביותר לצפייה היום"
    start  = report.find(marker)
    if start != -1:
        after = report[start + len(marker):]
        end   = after.find("\n## ")
        top5  = after[:end].strip() if end != -1 else after[:900].strip()
    else:
        top5 = report[:900]
    top5 = top5[:900]

    print(f"[send] Pushing notification + email for {path}")
    send_ntfy(f"📊 דוח שוקי ההון — {TODAY}", top5)

    subject = f"📊 דוח מודיעין שוקי ההון — {TODAY}"
    html    = md_to_html(report)
    send_email(subject, html)
    print("[send] Done")


# ── Main (legacy all-in-one pipeline) ────────────────────────────────────────

def main():
    print(f"[market-report] Starting — {TODAY}")

    print(f"[1/4] Running {len(QUERIES)} Tavily searches...")
    results = []
    for i, q in enumerate(QUERIES, 1):
        print(f"  [{i:02d}/{len(QUERIES)}] {q[:60]}")
        results.append(tavily_search(q))

    print("[2/4] Building Hebrew report...")
    report = build_report(results)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[3/4] Report saved → {REPORT_PATH}")

    marker = "## 🔥 5 הדברים החשובים ביותר לצפייה היום"
    start  = report.find(marker)
    if start != -1:
        after = report[start + len(marker):]
        end   = after.find("\n## ")
        top5  = after[:end].strip() if end != -1 else after[:900].strip()
    else:
        top5 = report[:900]
    top5 = top5[:900]

    print("[4/4] Sending notifications...")
    send_ntfy(f"📊 דוח שוקי ההון — {TODAY}", top5)

    subject  = f"📊 דוח מודיעין שוקי ההון — {TODAY}"
    html     = md_to_html(report)
    send_email(subject, html)

    print(f"[market-report] Done — {REPORT_PATH}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd == "collect":
        cmd_collect()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("usage: market_report.py search \"<query>\"", file=sys.stderr)
            sys.exit(1)
        cmd_search(sys.argv[2])
    elif cmd == "send":
        if len(sys.argv) < 3:
            print("usage: market_report.py send <report.md>", file=sys.stderr)
            sys.exit(1)
        cmd_send(sys.argv[2])
    else:
        main()
