# Morning Newsletter Bot — Product Vision

## What It Is
A personalized daily morning briefing delivered via SMS. Users text a number, set their interests,
and every morning they receive a smart digest covering news, sports, finance, and weather — plus
a link to a clean dashboard UI for the full view.

No app to download. Works on any phone. Just regular texting.

---

## Core Features

### 1. News Aggregator
- Pulls from RSS feeds (ESPN, CNN, BBC, Reuters, Google News, etc.)
- Reddit integration (r/nba, r/investing, r/worldnews, etc.)
- Filtered by each user's interests and followed sites
- Delivered as headline + 2-3 sentence summary

### 2. Sports Tracking
- Last night's scores and highlights
- Injury reports and player updates
- Team standings
- Fantasy-relevant stat lines
- Betting line movement (notable sharp action)

### 3. Finance Tracker
- Portfolio value and daily P&L
- Individual position performance
- Stocks on your watchlist hitting price levels
- Upcoming earnings for stocks you hold
- Crypto prices (if applicable)
- Fear & Greed index
- Connects to brokerage via Alpaca or Plaid API

### 4. Weather
- Daily forecast for your location
- Severe weather alerts
- Week ahead summary

### 5. AI Morning Briefing (Powered by Claude Haiku)
- Reads everything scraped that day
- Writes a 5-7 sentence "What you need to know today" summary
- Surfaces the most important story across all your categories
- Trend detection — flags when multiple sources cover the same topic
- Saves you from reading through everything yourself

---

## How It Works

```
7:00 AM — Scheduler runs
         ↓
Scrapes news, sports, finance, weather for each user
         ↓
Claude Haiku summarizes and writes morning briefing
         ↓
SMS sent to user with key highlights + dashboard link
         ↓
User can reply to ask follow-up questions
         ↓
User opens link → full personalized dashboard UI
```

---

## Cost Breakdown

### Per User Per Month

| Component             | Cost Per User/Month | Notes                              |
|-----------------------|--------------------|------------------------------------|
| Twilio SMS (sending)  | $0.47              | ~60 texts/month (2/day digest)     |
| Twilio SMS (receiving)| $0.47              | ~60 replies/month                  |
| Claude Haiku API      | $0.56              | Daily briefing + summaries         |
| Plaid (finance)       | $0.10              | Optional, only if finance enabled  |
| Hosting (per user)    | $0.43–$0.71        | Scales with user count             |
| **Total per user**    | **~$2.03–$2.31**   | Without finance: ~$1.93–$2.21      |

### Fixed Monthly Costs (regardless of user count)

| Component             | Cost/Month | Notes                              |
|-----------------------|------------|------------------------------------|
| Twilio phone number   | $1.15      | One number serves all users        |
| Hosting base          | $0–$5      | Railway.app free tier to start     |
| **Fixed total**       | **$1.15–$6.15** |                               |

### Total Cost by User Count

| Users | Monthly Cost | Cost Per User |
|-------|-------------|---------------|
| 5     | ~$12–$18    | ~$2.40–$3.60  |
| 10    | ~$22–$29    | ~$2.20–$2.90  |
| 25    | ~$52–$64    | ~$2.08–$2.56  |
| 50    | ~$103–$121  | ~$2.06–$2.42  |
| 100   | ~$204–$237  | ~$2.04–$2.37  |
| 500   | ~$1,016–$1,156 | ~$2.03–$2.31 |

> Cost per user stabilizes around $2.03–$2.31 at scale since fixed costs
> get spread across more users.

### Cost Saving Strategies
- **Article caching** — if 3 users follow NBA, summarize once, share across all 3 (~40% Claude cost reduction)
- **Batch scraping** — scrape shared sources once per run, not once per user
- **With caching at 50 users** — estimated ~$80–$95/month vs $103–$121 uncached

---

## Monetization Options (if you ever want to charge)

| Model                  | Price/User | Your Margin |
|------------------------|------------|-------------|
| Free (your cost)       | $0         | -$2.03/user |
| Break even             | $2.50/user | ~$0.20/user |
| Subscription (basic)   | $5/user    | ~$2.50–$3/user |
| Subscription (premium) | $10/user   | ~$7.50–$8/user |

---

## Build Order

| Phase | Feature                              | Status      |
|-------|--------------------------------------|-------------|
| 1     | SMS bot onboarding + user profiles   | Up next     |
| 2     | News aggregator + RSS scraper        | Up next     |
| 3     | Sports tracking (scores, injuries)   | Planned     |
| 4     | AI morning briefing (Claude Haiku)   | Planned     |
| 5     | Weather integration                  | Planned     |
| 6     | Finance tracker + portfolio summary  | Planned     |
| 7     | Full dashboard UI                    | Planned     |

---

## APIs & Services Needed

| Service         | Purpose                  | Cost          | Signup                        |
|-----------------|--------------------------|---------------|-------------------------------|
| Twilio          | SMS send/receive         | ~$1.15+/month | twilio.com                    |
| Claude API      | AI summaries + briefing  | Pay per token | console.anthropic.com         |
| Plaid           | Brokerage/bank access    | $0.10/user    | plaid.com                     |
| Alpaca          | Brokerage (alternative)  | Free          | alpaca.markets                |
| Open-Meteo      | Weather                  | Free          | open-meteo.com                |
| Reddit (PRAW)   | Reddit scraping          | Free          | reddit.com/prefs/apps         |
| RSS Feeds       | News sites               | Free          | No signup needed              |
| Railway.app     | Hosting                  | Free tier     | railway.app                   |
