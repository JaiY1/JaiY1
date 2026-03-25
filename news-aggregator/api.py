"""
News Aggregator API
-------------------
Central service exposing news, user management, digests, and cost tracking.
Other projects (SMS bot, dashboard, NBA tool) hit this API.

Endpoints:
  POST /users                     - create user
  GET  /users/<phone>             - get user profile
  PUT  /users/<phone>             - update interests/sources/subreddits
  GET  /users/<phone>/digest      - get today's digest for a user
  POST /digest/run                - manually trigger digest for all users
  GET  /articles?category=nba     - get latest articles by category
  GET  /costs                     - get API cost summary
  GET  /costs/total               - get total spend this month
"""

from flask import Flask, request, jsonify
from database import (
    init_db, create_user, get_user, update_user, get_all_users,
    get_articles_for_user, mark_articles_sent, get_cost_summary
)
from scraper import scrape_all, save_articles
from summarizer import summarize_batch, write_morning_briefing
import sqlite3
import os

app = Flask(__name__)
init_db()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newsletter.db")


# --- User endpoints ---

@app.route("/users", methods=["POST"])
def create_user_route():
    data = request.json
    phone = data.get("phone_number", "").strip()
    name = data.get("name", "").strip()
    if not phone:
        return jsonify({"error": "phone_number required"}), 400
    create_user(phone, name)
    return jsonify(get_user(phone))


@app.route("/users/<phone>", methods=["GET"])
def get_user_route(phone):
    user = get_user(phone)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/users/<phone>", methods=["PUT"])
def update_user_route(phone):
    user = get_user(phone)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.json
    allowed = ["name", "interests", "sources", "subreddits", "location"]
    updates = {k: v for k, v in data.items() if k in allowed}
    update_user(phone, **updates)
    return jsonify(get_user(phone))


# --- Digest endpoints ---

@app.route("/users/<phone>/digest", methods=["GET"])
def get_digest(phone):
    user = get_user(phone)
    if not user:
        return jsonify({"error": "User not found"}), 404

    interests = user["interests"] or ["world news"]

    # Scrape + save fresh articles
    articles = scrape_all(interests)
    save_articles(articles)

    # Fetch unsent articles
    unsent = get_articles_for_user(user["id"], interests, limit=10)
    if not unsent:
        return jsonify({"briefing": "No new articles today.", "articles": []})

    summarized = summarize_batch(unsent)
    briefing = write_morning_briefing(summarized, user.get("name"))
    mark_articles_sent(user["id"], [a["id"] for a in summarized])

    return jsonify({
        "user": user["name"] or phone,
        "briefing": briefing,
        "articles": [
            {
                "title": a["title"],
                "category": a["category"],
                "summary": a.get("summary"),
                "url": a["url"],
                "source": a["source"],
            }
            for a in summarized
        ]
    })


@app.route("/digest/run", methods=["POST"])
def run_all_digests():
    """Trigger digest for all users — called by scheduler or manually."""
    users = get_all_users()
    if not users:
        return jsonify({"message": "No users found."}), 200

    all_interests = list({i for u in users for i in u["interests"]})
    articles = scrape_all(all_interests)
    save_articles(articles)

    results = []
    for user in users:
        interests = user["interests"] or ["world news"]
        unsent = get_articles_for_user(user["id"], interests, limit=10)
        if unsent:
            summarized = summarize_batch(unsent)
            briefing = write_morning_briefing(summarized, user.get("name"))
            mark_articles_sent(user["id"], [a["id"] for a in summarized])
            results.append({"user": user["name"] or user["phone_number"], "articles_sent": len(summarized)})
        else:
            results.append({"user": user["name"] or user["phone_number"], "articles_sent": 0})

    return jsonify({"results": results})


# --- Articles endpoint ---

@app.route("/articles", methods=["GET"])
def get_articles():
    category = request.args.get("category", "").strip()
    limit = int(request.args.get("limit", 20))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM articles"
    params = []
    if category:
        query += " WHERE LOWER(category) LIKE ?"
        params.append(f"%{category.lower()}%")
    query += " ORDER BY scraped_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# --- Cost tracking endpoints ---

@app.route("/costs", methods=["GET"])
def get_costs():
    return jsonify(get_cost_summary())


@app.route("/costs/total", methods=["GET"])
def get_total_costs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT
            service,
            SUM(cost_usd) as total_usd,
            COUNT(*) as api_calls,
            SUM(units) as total_tokens,
            strftime('%Y-%m', logged_at) as month
        FROM api_costs
        WHERE strftime('%Y-%m', logged_at) = strftime('%Y-%m', 'now')
        GROUP BY service
    """).fetchall()
    overall = conn.execute(
        "SELECT SUM(cost_usd) as grand_total FROM api_costs WHERE strftime('%Y-%m', logged_at) = strftime('%Y-%m', 'now')"
    ).fetchone()
    conn.close()
    return jsonify({
        "month": "current",
        "grand_total_usd": round(overall["grand_total"] or 0, 6),
        "breakdown": [dict(r) for r in rows]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
