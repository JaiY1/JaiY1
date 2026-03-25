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


def write_morning_briefing(articles: list[dict], user_name: str = None) -> str:
    """Write a 5-7 sentence AI morning briefing from the day's top articles."""
    if not articles:
        return "No news found for your interests today."

    headlines = "\n".join([
        f"- [{a['category'].upper()}] {a['title']}: {a.get('summary') or a.get('excerpt', '')[:150]}"
        for a in articles[:15]
    ])

    greeting = f"Good morning{' ' + user_name if user_name else ''}!"
    prompt = f"""You are writing a short morning briefing. In 5-7 sentences, summarize the most important stories from the headlines below. Be conversational, concise, and cover the most impactful stories. Start with "{greeting}".

Headlines:
{headlines}

Morning briefing:"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        briefing = response.content[0].text.strip()

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)
        log_cost("claude-haiku", "morning_briefing", input_tokens + output_tokens, cost)

        return briefing

    except Exception as e:
        print(f"  Morning briefing failed: {e}")
        return f"{greeting} Here are today's top stories."


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
