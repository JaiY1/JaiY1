import anthropic
from database import log_cost
from config import ANTHROPIC_API_KEY

# Haiku 4.5 pricing
INPUT_COST_PER_TOKEN = 0.80 / 1_000_000
OUTPUT_COST_PER_TOKEN = 4.00 / 1_000_000

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Cache: url -> summary (avoids re-summarizing same article for multiple users)
_summary_cache = {}


def summarize_article(title: str, excerpt: str, url: str) -> str:
    if url in _summary_cache:
        return _summary_cache[url]

    if not excerpt:
        return title

    prompt = f"""Summarize this news article in 2 sentences. Be concise and factual.

Title: {title}
Content: {excerpt}

Summary:"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text.strip()

        # Log cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)
        log_cost("claude-haiku", "summarize_article", input_tokens + output_tokens, cost)

        _summary_cache[url] = summary
        return summary

    except Exception as e:
        print(f"  Summarization failed: {e}")
        return excerpt[:200] + "..." if len(excerpt) > 200 else excerpt


def write_morning_briefing(articles: list[dict], user_name: str = None) -> list[dict]:
    """
    Write a bullet-point morning briefing. Returns a list of dicts:
    [{"point": "...", "category": "iran", "keywords": ["iran", "missile"]}]
    Each bullet is clickable and links to articles in that category.
    """
    if not articles:
        return [{"point": "No news found for your interests today.", "category": "", "keywords": []}]

    headlines = "\n".join([
        f"- [{a['category'].upper()}] {a['title']}"
        for a in articles[:15]
    ])

    prompt = f"""You are writing a morning briefing as bullet points. Each bullet covers one key story or theme from the headlines below.

Return ONLY a JSON array like this (no extra text):
[
  {{"point": "One sentence summary of the story.", "category": "the category name from the headlines", "keywords": ["keyword1", "keyword2"]}},
  ...
]

Write 5-7 bullets. Be concise and factual. Use the exact category name from the headlines (e.g. "iran", "ai", "arsenal", "timberwolves").

Headlines:
{headlines}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        import json
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        bullets = json.loads(text)

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)
        log_cost("claude-haiku", "morning_briefing", input_tokens + output_tokens, cost)

        return bullets

    except Exception as e:
        print(f"  Morning briefing failed: {e}")
        # Fallback: one bullet per category
        seen = set()
        bullets = []
        for a in articles[:5]:
            if a["category"] not in seen:
                seen.add(a["category"])
                bullets.append({"point": a["title"], "category": a["category"], "keywords": []})
        return bullets


def summarize_batch(articles: list[dict]) -> list[dict]:
    """Summarize a list of articles, skip ones already cached."""
    for article in articles:
        if not article.get("summary"):
            print(f"  Summarizing: {article['title'][:60]}...")
            article["summary"] = summarize_article(
                article["title"],
                article.get("excerpt", ""),
                article["url"]
            )
    return articles
